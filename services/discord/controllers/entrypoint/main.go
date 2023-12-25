package main

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"

	"cloud.google.com/go/pubsub"
)

var cloudProjectID = os.Getenv("CLOUD_PROJECT_ID")
var discordPublicKey = os.Getenv("DISCORD_PUBLIC_KEY")

type Interaction struct {
	Type InteractionType `json:"type"`
	Data InteractionData `json:"data"`
}

type InteractionData struct {
	Name    string                        `json:"name"`
	Type    *ApplicationCommandOptionType `json:"type"`
	Focused *bool                         `json:"focused"`
	Options []InteractionData             `json:"options"`
}

type InteractionType int

type interactionTypes struct {
	Ping                           InteractionType
	ApplicationCommand             InteractionType
	MessageComponent               InteractionType
	ApplicationCommandAutoComplete InteractionType
	ModalSubmit                    InteractionType
}

var InteractionTypes = interactionTypes{
	Ping:                           1,
	ApplicationCommand:             2,
	MessageComponent:               3,
	ApplicationCommandAutoComplete: 4,
	ModalSubmit:                    5,
}

type ApplicationCommandOptionType int

type applicationCommandOptionTypes struct {
	SubCommand      ApplicationCommandOptionType
	SubCommandGroup ApplicationCommandOptionType
	String          ApplicationCommandOptionType
	Integer         ApplicationCommandOptionType
	Boolean         ApplicationCommandOptionType
	User            ApplicationCommandOptionType
	Channel         ApplicationCommandOptionType
	Role            ApplicationCommandOptionType
	Mentionable     ApplicationCommandOptionType
	Number          ApplicationCommandOptionType
	Attachment      ApplicationCommandOptionType
}

var ApplicationCommandOptionTypes = applicationCommandOptionTypes{
	SubCommand:      1,
	SubCommandGroup: 2,
	String:          3,
	Integer:         4,
	Boolean:         5,
	User:            6,
	Channel:         7,
	Role:            8,
	Mentionable:     9,
	Number:          10,
	Attachment:      11,
}

const readLimit = 10 * 1024 * 1024

func verifyKey(publicKey ed25519.PublicKey, timestamp string, signature []byte, body []byte) (bool, error) {
	var message = bytes.NewBufferString(timestamp)
	if count, err := message.Write(body); err != nil {
		return false, err
	} else if count != len(body) {
		return false, fmt.Errorf(`failed write to message buffer`)
	} else if verified := ed25519.Verify(publicKey, message.Bytes(), signature); !verified {
		return false, fmt.Errorf(`failed ed25519 verification`)
	} else {
		return true, nil
	}
}

func verify(publicKey ed25519.PublicKey) func(func(http.ResponseWriter, *http.Request)) func(http.ResponseWriter, *http.Request) {
	return func(next func(http.ResponseWriter, *http.Request)) func(http.ResponseWriter, *http.Request) {
		return func(writer http.ResponseWriter, request *http.Request) {
			if request.Method != http.MethodPost {
				writer.WriteHeader(http.StatusMethodNotAllowed)
			} else if contentType := request.Header.Get(`Content-Type`); contentType != `application/json` {
				writer.WriteHeader(http.StatusBadRequest)
			} else if hexSignature := request.Header.Get(`X-Signature-Ed25519`); len(hexSignature) <= 0 {
				writer.WriteHeader(http.StatusBadRequest)
			} else if signature, err := hex.DecodeString(hexSignature); err != nil {
				writer.WriteHeader(http.StatusBadRequest)
			} else if len(signature) != ed25519.SignatureSize {
				writer.WriteHeader(http.StatusBadRequest)
			} else if timestamp := request.Header.Get(`X-Signature-Timestamp`); len(timestamp) <= 0 {
				writer.WriteHeader(http.StatusBadRequest)
			} else if body, err := io.ReadAll(io.LimitReader(request.Body, readLimit)); err != nil {
				writer.WriteHeader(http.StatusInternalServerError)
			} else if len(body) >= readLimit {
				writer.WriteHeader(http.StatusBadRequest)
			} else if verified, err := verifyKey(publicKey, timestamp, signature, body); err != nil {
				writer.WriteHeader(http.StatusInternalServerError)
			} else if !verified {
				writer.Write([]byte(`Unauthorized`))
				writer.WriteHeader(http.StatusBadRequest)
			} else {
				request.Body = io.NopCloser(bytes.NewBuffer(body))
				next(writer, request)
			}
		}
	}
}

func getInteractionName(interaction Interaction, dataOption *InteractionData) (name string) {
	var IterativeOptions []InteractionData
	if dataOption == nil {
		name = interaction.Data.Name
		IterativeOptions = interaction.Data.Options
	} else {
		name = dataOption.Name
		IterativeOptions = dataOption.Options
	}

	for i, option := range IterativeOptions {
		if option.Focused != nil && *option.Focused {
			continue
		} else if option.Type == nil {
			continue
		} else if *option.Type == ApplicationCommandOptionTypes.SubCommandGroup || *option.Type == ApplicationCommandOptionTypes.SubCommand {
			return name + "-" + getInteractionName(interaction, &IterativeOptions[i])
		}
	}

	return name
}

func runApplicationCommand(ctx context.Context, interaction Interaction, data []byte) (err error) {
	var commandName = getInteractionName(interaction, nil)

	var topic = pubsubClient.Topic(fmt.Sprintf("wikia-discord-commands-%s", commandName))

	var resp = topic.Publish(ctx, &pubsub.Message{
		Data: data,
	})

	if _, err = resp.Get(ctx); err != nil {
		return fmt.Errorf("pubsub: result.Get: %v", err)
	} else {
		return nil
	}
}

var pubsubClient *pubsub.Client

func main() {
	var err error
	var ctx = context.Background()

	if pubsubClient, err = pubsub.NewClient(ctx, cloudProjectID); err != nil {
		log.Fatalf("pubsub.NewClient: %v", err)
	} else if decodedDiscordPublicKey, err := hex.DecodeString(discordPublicKey); err != nil {
		log.Fatalf("unable to decode public key: %v", err)
	} else {
		http.HandleFunc("/discord/interactions/entrypoint", verify(decodedDiscordPublicKey)(entryPoint))

		if err := http.ListenAndServe(":8080", nil); err != nil {
			log.Fatalf("could not start server: %v", err)
		}
	}
}

func entryPoint(writer http.ResponseWriter, request *http.Request) {
	var interaction Interaction

	if body, err := io.ReadAll(request.Body); err != nil {
		writer.WriteHeader(http.StatusInternalServerError)
	} else if err := json.Unmarshal(body, &interaction); err != nil {
		writer.WriteHeader(http.StatusInternalServerError)
	} else if interaction.Type == InteractionTypes.Ping {
		writer.Header().Add("Content-Type", "application/json")
		writer.WriteHeader(http.StatusOK)
		writer.Write([]byte(`{"type": 1}`))
	} else if interaction.Type == InteractionTypes.ApplicationCommand {
		if err := runApplicationCommand(request.Context(), interaction, body); err != nil {
			log.Println(err)
			writer.WriteHeader(http.StatusInternalServerError)
		} else {
			writer.Header().Add("Content-Type", "application/json")
			writer.WriteHeader(http.StatusOK)
			writer.Write([]byte(`{"type": 5}`))
		}
	} else {
		writer.WriteHeader(http.StatusUnprocessableEntity)
	}
}

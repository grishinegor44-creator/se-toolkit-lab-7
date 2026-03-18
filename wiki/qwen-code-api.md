# `Qwen Code` API

<h2>Table of contents</h2>

- [What is `Qwen Code` API](#what-is-qwen-code-api)
- [Set up the `Qwen Code` API (REMOTE)](#set-up-the-qwen-code-api-remote)
  - [Set up the `Qwen Code` CLI (REMOTE)](#set-up-the-qwen-code-cli-remote)
  - [Clone the `Qwen Code` API repository (REMOTE)](#clone-the-qwen-code-api-repository-remote)
  - [Pull the latest changes from the `Qwen Code` API repository (REMOTE)](#pull-the-latest-changes-from-the-qwen-code-api-repository-remote)
  - [Enter the `Qwen Code` API repository directory (REMOTE)](#enter-the-qwen-code-api-repository-directory-remote)
  - [Prepare the environment in the `Qwen Code` API repository (REMOTE)](#prepare-the-environment-in-the-qwen-code-api-repository-remote)
  - [Start the `Qwen Code` API (REMOTE)](#start-the-qwen-code-api-remote)
  - [Check that the `Qwen Code` API is accessible (REMOTE)](#check-that-the-qwen-code-api-is-accessible-remote)

## What is `Qwen Code` API

<!-- TODO visualize -->

The `Qwen Code` API is an [OpenAI-compatible API](./llm.md#openai-compatible-api) that uses the [`Qwen Code` credentials file](./qwen-code.md#qwen-code-credentials-file) to provide access to the [`Qwen` API](./qwen-code.md#qwen-api).

The `Qwen Code` API is deployed using [`qwen-code-api`](https://github.com/inno-se-toolkit/qwen-code-api).

## Set up the `Qwen Code` API (REMOTE)

Complete these steps:

1. [Set up the `Qwen Code` CLI (REMOTE)](#set-up-the-qwen-code-cli-remote).
2. [Clone the `Qwen Code` API repository (REMOTE)](#clone-the-qwen-code-api-repository-remote).
3. [Pull the latest changes from the `Qwen Code` API repository (REMOTE)](#pull-the-latest-changes-from-the-qwen-code-api-repository-remote).
4. [Enter the `Qwen Code` API repository directory (REMOTE)](#enter-the-qwen-code-api-repository-directory-remote).
5. [Prepare the environment in the `Qwen Code` API repository (REMOTE)](#prepare-the-environment-in-the-qwen-code-api-repository-remote).
6. [Start the `Qwen Code` API (REMOTE)](#start-the-qwen-code-api-remote).
7. [Check that the `Qwen Code` API is accessible (REMOTE)](#check-that-the-qwen-code-api-is-accessible-remote).

### Set up the `Qwen Code` CLI (REMOTE)

1. [Connect to the VM](./vm-access.md#connect-to-the-vm).

2. [Install `Node.js`](./nodejs.md#install-nodejs).

3. [Install `pnpm`](./nodejs.md#install-pnpm).

4. To install [`Qwen Code`](./qwen-code.md#what-is-qwen-code),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   pnpm add -g @qwen-code/qwen-code
   ```

5. [Open a chat with `Qwen Code` using the CLI](./qwen-code.md#open-a-chat-with-qwen-code-using-the-cli).

6. Type `/auth` in the chat to [authenticate via Qwen OAuth](https://github.com/QwenLM/qwen-code?tab=readme-ov-file#authentication).

7. Open the link in a browser to complete the authentication procedure.

8. [Quit the chat with `Qwen Code`](./qwen-code.md#quit-the-chat-with-qwen-code).

### Clone the `Qwen Code` API repository (REMOTE)

1. To [clone using the `VS Code Terminal` the repo](./git-vscode.md#clone-the-repo-using-the-vs-code-terminal)

   <https://github.com/inno-se-toolkit/qwen-code-api>,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git clone https://github.com/inno-se-toolkit/qwen-code-api ~/qwen-code-api
   ```

### Pull the latest changes from the `Qwen Code` API repository (REMOTE)

1. To pull the latest changes,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   git pull
   ```

### Enter the `Qwen Code` API repository directory (REMOTE)

1. To enter the repository directory,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cd ~/qwen-code-api
   ```

### Prepare the environment in the `Qwen Code` API repository (REMOTE)

1. To create the [`.env`](./file-formats.md#env) file,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   cp .env.example .env
   ```

2. To open the `.env` file in `nano`,

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   nano .env
   ```

3. Write an arbitrary value for `QWEN_CODE_API_KEY`.

   This key will protect your `Qwen Code` API.

4. Save the file (`Ctrl + O`).

### Start the `Qwen Code` API (REMOTE)

1. To start the `Qwen Code` API via [`Docker Compose`](./docker-compose.md#what-is-docker-compose),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   docker compose up --build -d
   ```

### Check that the `Qwen Code` API is accessible (REMOTE)

1. To send an [`HTTP` request](./http.md#http-request) to the [`Qwen Code` API](#what-is-qwen-code-api),

   [run in the `VS Code Terminal`](./vs-code.md#run-a-command-in-the-vs-code-terminal):

   ```terminal
   curl -s http://localhost:<qwen-code-api-host-port>/v1/chat/completions \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <qwen-code-api-key>" \
     -d '{"model":"<qwen-model>","messages":[{"role":"user","content":"What is 2+2?"}]}' \
     | jq .
   ```

   Replace placeholders:

   - `<qwen-code-api-host-port>` with the value of [`QWEN_CODE_API_HOST_PORT`](./qwen-code-api-dotenv-secret.md#qwen_code_api_host_port) from [`~/qwen-code-api/.env.secret` (REMOTE)](./qwen-code-api-dotenv-secret.md#about-qwen-code-apienvsecret)
   - `<qwen-code-api-key>` with the value of [`QWEN_CODE_API_KEY`](./qwen-code-api-dotenv-secret.md#qwen_code_api_key) from [`~/qwen-code-api/.env.secret` (REMOTE)](./qwen-code-api-dotenv-secret.md#about-qwen-code-apienvsecret)
   - `<qwen-model>` with one of the [available models](./qwen-code.md#view-available-models)

2. When you run it, the output should be similar to this:

   ```terminal
   {
      "created": 1773379590,
      "usage": {
         "completion_tokens": 8,
         "prompt_tokens": 15,
         "prompt_tokens_details": {
            "cached_tokens": 0
         },
         "total_tokens": 23
      },
      "model": "coder-model",
      "id": "chatcmpl-9c04fd89-7d16-469f-af7b-8e64a9418bb3",
      "choices": [
         {
            "finish_reason": "stop",
            "index": 0,
            "message": {
            "role": "assistant",
            "content": "2 + 2 = 4."
            }
         }
      ],
      "object": "chat.completion"
   }
   ```

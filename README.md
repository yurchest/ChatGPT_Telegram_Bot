# ChatGpt Telegram Bot

This project is a Telegram bot based on GPT, which can answer user questions and perform various tasks. The bot supports subscriptions and trial periods for users.

## Detailed Description

The ChatGpt Telegram Bot is an advanced conversational agent built using the GPT model from OpenAI. This bot is designed to interact with users in a natural and engaging manner, providing answers to questions, performing tasks, and offering assistance on a wide range of topics. The bot is integrated with several technologies to enhance its functionality, reliability, and scalability.

### Key Features

1. **Natural Language Processing**: Leveraging the power of GPT, the bot can understand and respond to user queries in a human-like manner.
2. **Subscription Management**: Users can subscribe to the bot's services, with support for trial periods and subscription renewals.
3. **Database Integration**: User data, subscription details, and payment information are securely stored in a PostgreSQL database.
4. **Redis Caching**: Redis is used to store message history and manage request states, ensuring quick and efficient data retrieval.
5. **Dockerized Deployment**: The entire application is containerized using Docker, making it easy to deploy and manage across different environments.
6. **Continuous Integration/Continuous Deployment (CI/CD)**: GitHub Actions are used to automate the deployment process, ensuring that updates are seamlessly integrated and deployed.
7. **Monitoring and Metrics**: Integration with Prometheus and Grafana for monitoring bot performance and metrics.

### Technologies Used

- **Python**: The main programming language of the project, chosen for its simplicity and extensive libraries.
- **Aiogram**: A powerful library for creating Telegram bots, providing a robust framework for handling bot interactions.
- **OpenAI API**: Used for generating responses based on the GPT model, enabling the bot to understand and respond to user queries effectively.
- **SQLAlchemy**: An Object-Relational Mapping (ORM) library for working with the PostgreSQL database, simplifying database interactions.
- **PostgreSQL**: The primary database for storing user and payment information, chosen for its reliability and performance.
- **Redis**: Used for storing message history and managing request states, providing fast data access and caching capabilities.
- **Docker**: Containerization of the application for easier deployment and dependency management, ensuring consistency across different environments.
- **Docker Compose**: A tool for managing multi-container Docker applications, simplifying the orchestration of the bot, database, and caching services.
- **GitHub Actions**: CI/CD for automatic deployment of the application, ensuring that updates are tested and deployed seamlessly.
- **pytest**: A framework for testing, ensuring the reliability and correctness of the codebase.
- **Prometheus**: Used for collecting and storing metrics, providing insights into the bot's performance.
- **Grafana**: A visualization tool for displaying metrics collected by Prometheus, enabling easy monitoring and analysis.

### Benefits of the Project

1. **Enhanced User Interaction**: The bot provides a seamless and engaging user experience, making it easy for users to get the information they need.
2. **Scalability**: The use of Docker and Docker Compose ensures that the application can be easily scaled to handle increased user load.
3. **Reliability**: The integration of PostgreSQL and Redis ensures that user data is stored securely and can be accessed quickly.
4. **Ease of Deployment**: The use of Docker and GitHub Actions simplifies the deployment process, making it easy to deploy updates and manage the application.
5. **Extensibility**: The modular design of the bot and the use of Aiogram make it easy to add new features and extend the functionality of the bot.
6. **Monitoring and Insights**: The integration with Prometheus and Grafana provides detailed insights into the bot's performance and usage.

By leveraging these technologies, the ChatGpt Telegram Bot provides a powerful and flexible solution for interacting with users, managing subscriptions, and handling payments. This project demonstrates the potential of combining advanced natural language processing with robust backend technologies to create a seamless and engaging user experience.

## Database Tables


### users

| Field               | Data Type           | Description                          |
|---------------------|---------------------|--------------------------------------|
| `telegram_id`       | BigInteger          | Unique user identifier (primary key) |
| `first_name`        | String(255)         | User's first name                    |
| `username`          | String(255)         | User's Telegram username             |
| `language_code`     | String(127)         | Language code                        |
| `register_date`     | DateTime(timezone=True) | Registration date                   |
| `num_requests`      | BigInteger          | Number of user requests              |
| `num_input_tokens`  | BigInteger          | Number of input tokens               |
| `num_output_tokens` | BigInteger          | Number of output tokens              |
| `sub_expiration_date` | DateTime(timezone=True) | Subscription expiration date       |

### payments

| Field                         | Data Type           | Description                          |
|-------------------------------|---------------------|--------------------------------------|
| `id`                           | Integer             | Unique payment identifier (primary key) |
| `telegram_id`                  | BigInteger          | User's Telegram identifier           |
| `telegram_username`            | String(255)         | User's Telegram username             |
| `create_date`                  | DateTime(timezone=True) | Payment creation date               |
| `currency`                     | String(100)         | Payment currency                     |
| `total_amount`                 | Integer             | Total payment amount                 |
| `telegram_payment_charge_id`   | String             | Telegram payment charge identifier   |
| `provider_payment_charge_id`   | String             | Provider payment charge identifier   |
| `invoice_payload`              | String             | Invoice information                  |
| `is_recurring`                 | String             | Recurring payment flag               |
| `subscription_expiration_date` | DateTime(timezone=True) | Subscription expiration date       |
| `is_first_recurring`           | String             | First recurring payment flag         |
| `order_info`                   | String             | Order information                    |

### errors

| Field              | Data Type           | Description                          |
|--------------------|---------------------|--------------------------------------|
| `id`               | Integer             | Unique error identifier (primary key) |
| `type`             | String(255)         | Error type                           |
| `text`             | String              | Error description                    |
| `file_path`        | String              | Path to the file where the error occurred |
| `telegram_id`      | BigInteger          | User's Telegram identifier           |
| `create_date`      | DateTime(timezone=True) | Error occurrence date               |
| `traceback`        | String              | Error traceback                      |
| `is_resolved`      | Boolean             | Flag indicating if the error is resolved |
 
## Deployment Steps

To deploy the ChatGpt Telegram Bot service to production, follow these steps:

1. **Install Docker** ([Official Guide](https://docs.docker.com/engine/install/ubuntu/))


* Remove Conflicting Packages:
  ```sh
  for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done
  ```

* Add Docker's Official GPG Key:
  ```sh
  sudo apt-get update
  sudo apt-get install ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  ```

* Add Docker Repository to Apt Sources:
  ```sh
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  ```


* Install Docker from apt:
  ```sh
  sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
  ```

2. **Clone Repo**
  ```sh
  git clone https://github.com/yurchest/ChatGPT_Telegram_Bot.git
  ```
3. **Set Configuration File**

This is a configuration file for a Telegram bot project. It contains sensitive information such as API keys, database credentials, and other configuration parameters. Below is a description of the file with all sensitive parameters hidden:

```properties
// filepath: ./.env

# Telegram Bot Token
TELEGRAM_BOT_TOKEN=***************

# OpenAI API Key
OPENAI_API_KEY=***************

# YooKassa Payment Token
# YOOKASSA_PAYMENT_TOKEN=***************
YOOKASSA_PAYMENT_TOKEN=***************

# PostgreSQL Database Configuration
POSTGRES_DB=***************
POSTGRES_USER=***************
POSTGRES_PASSWORD=***************

# pgAdmin Configuration
PGADMIN_DEFAULT_EMAIL=***************
PGADMIN_DEFAULT_PASSWORD=***************

# Redis Configuration
REDIS_PORT=***************
REDIS_HOST=***************
REDIS_USER=***************
REDIS_USER_PASSWORD=***************
REDIS_PASSWORD=***************

# Subscription Configuration
SUBSCRIPTION_DURATION_MONTHS=***************
TRIAL_PERIOD_NUM_REQ=***************
SUBSCRIPTION_PRICE_RUB=***************

# Billing Email
EMAIL_FOR_BILL=***************
```
4. **Transfer Environment Variables**:
  ```sh
  scp -P <PORT> .env root@<server_ip>:/root/ChatGPT_Telegram_Bot
  ```

5. **Deploy the Service**:
 - Navigate to the project directory:
    ```sh
    cd /root/ChatGPT_Telegram_Bot
    ```
  - Build and start the Docker containers:
    ```sh
    sudo docker-compose up --build -d
    ```

6. **Verify Deployment**:
  - Check the status of the containers:
    ```sh
    sudo docker ps
    ```
  - Ensure the service is running correctly by accessing the logs:
    ```sh
    sudo docker-compose logs -f
    ```

By following these steps, you will successfully deploy the ChatGpt Telegram Bot service to production.
## CI/CD
### Setting up GitHub Actions

To set up GitHub Actions for CI/CD, follow these steps:

1. **Create a GitHub Repository**:
    - Navigate to GitHub and create a new repository or use an existing one.

2. **Setting Up SSH Access for GitHub Actions**  
To allow GitHub Actions to connect to the server via SSH and execute commands, you need to configure SSH keys.
  
    - **Generating an SSH Key** (if you don't have one)  
  On your **local computer** (from where you push code), run the following command:  

      ```sh
      ssh-keygen -t ed25519 -C "github-actions"
      ```
      Press `Enter` when it asks for a path (`~/.ssh/id_ed25519` by default).  
      **Do not set a password**, just press `Enter`.  

      After that, two files will appear in the `~/.ssh/` folder:  
      - `id_ed25519` — **private key** (don't share it!)  
      - `id_ed25519.pub` — **public key** (we'll add this to the server)



    - **Adding the Public Key to the Server**
Now you need to add the contents of `id_ed25519.pub` to the server.

        1. Connect to the server manually:  
        ```sh
        ssh user@your-server-ip
        ```
      2. Open the authorized keys file:  
      ```sh
      nano ~/.ssh/authorized_keys
      ```
      3. Paste the contents of `id_ed25519.pub` into it.  
      4. Save it (`Ctrl + X → Y → Enter`).  

      Make sure the permissions are correct for `.ssh` and `authorized_keys`:  
      ```sh
      chmod 700 ~/.ssh
      chmod 600 ~/.ssh/authorized_keys
      ```

    Now you can connect without a password:  
    ```sh
    ssh user@your-server-ip
    ```

    - **Adding SSH Key to GitHub Secrets**
    
      To allow GitHub Actions to use this key:

      1. Go to **GitHub → Settings → Secrets and variables → Actions**.  
      2. Create a **new secret** (`New repository secret`):  
        - **Name:** `SSH_KEY`  
        - **Value:** The content of `id_ed25519` (the private key).  
      3. Also add:  
        - `SSH_HOST` → The IP address or domain of the server.  
        - `SSH_USER` → The user (e.g., `root` or `ubuntu`).  



3. **Create GitHub Actions Workflow**:
  - In your repository, create a `.github/workflows` directory.
  - Create a new workflow file, e.g., [deploy.xml](https://github.com/yurchest/ChatGPT_Telegram_Bot/blob/main/.github/workflows/deploy.yml):


By following these steps, you will set up GitHub Actions for continuous integration and deployment of your ChatGpt Telegram Bot service.



To perform `git pull` without entering a username and password, you can set up authentication using either an SSH key or a Personal Access Token (PAT), depending on how your Git server is configured. Here's how to do it for each method:

### Git Pull without Password using an SSH Key

1. **Generate an SSH key** (if you don't have one):
   Open the terminal and run:
   ```bash
   ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
   ```
   Specify the path to save the key, e.g., `~/.ssh/id_rsa`, and create a password for the key if desired.

2. **Add the public key to GitHub (or another Git server)**:
   Copy the contents of your public key:
   ```bash
   cat ~/.ssh/id_rsa.pub
   ```
   Go to your GitHub account, open the settings (Settings), select **SSH and GPG keys**, and add a new key by pasting the copied key.

3. **Test the SSH connection**:
   To check if the SSH key is set up correctly, run:
   ```bash
   ssh -T git@github.com
   ```
   If successful, you will see a message like:
   ```bash
   Hi username! You've successfully authenticated, but GitHub does not provide shell access.
   ```

4. **Use the SSH URL for the repository**:
   Change the repository URL to the SSH format:
   ```bash
   git remote set-url origin git@github.com:username/repository.git
   ```

Now, when you run `git pull`, it will use the SSH key for authentication, and you won’t need to enter your username and password.



<details><summary>

## Local GitHub Hooks

</summary>
<br>

  1. Placed in `.git/hooks/pre-push`

     Prevents local pushes to the `main` branch:
     ```bash
     #!/bin/bash
     branch=$(git rev-parse --abbrev-ref HEAD)
     if [ "$branch" = "main" ]; then
       echo "You cannot push directly to main. Use a Pull Request!"
       exit 1
     fi 
     ```
     Ensure the script has write permissions to work correctly.

</details>





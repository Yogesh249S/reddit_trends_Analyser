
# RedditStream Analytics

A cloud-native microservices pipeline for ingesting Reddit data, processing it with sentiment analysis, storing it in PostgreSQL, and visualizing it via Streamlit — containerized and deployable to AWS using Terraform and ECS Fargate.

---

## 🧱 Project Structure

```
.
├── ingestion/           # Fetches data from Reddit and sends to Kafka
├── processing/          # Processes Kafka messages, stores results in PostgreSQL
├── dashboard/           # Streamlit app for visualizing sentiment data
├── docker-compose.yml   # For local development
├── terraform/           # Infrastructure as Code for AWS
├── .github/workflows/   # GitHub Actions for CI/CD
```

---

## 🛠️ Prerequisites

- Docker & Docker Compose
- Python 3.10+
- AWS CLI & credentials set
- Terraform >= 1.0
- Reddit API credentials

---

## 🚀 Phase 1: Run Locally with Docker Compose

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/redditstream-analytics.git
cd redditstream-analytics
```

### 2. Set up environment variables

Create a `.env` file in the root directory:

```env
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
REDDIT_USER_AGENT=your_user_agent
POSTGRES_USER=reddit
POSTGRES_PASSWORD=reddit
POSTGRES_DB=reddit
```

### 3. Start services
```bash
docker-compose up --build
```

- Access the dashboard at: [http://localhost:8501](http://localhost:8501)
- Kafka and PostgreSQL run in containers and are linked to the ingestion and processing services.

---

## 🚢 Phase 2: CI/CD with GitHub Actions

- GitHub Actions is set up to:
  - Build Docker images for each service
  - Push to Amazon ECR
  - Trigger ECS deploy on push to `main`
- Set the following secrets in your GitHub repo:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `AWS_ACCOUNT_ID`
  - `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`

---

## ☁️ Phase 3: Deploy to AWS (Terraform + ECS Fargate)

### 1. Initialize Terraform

```bash
cd terraform
terraform init
```

### 2. Set variables (via `terraform.tfvars` or CLI)

```hcl
aws_region        = "eu-north-1"
aws_account_id    = "YOUR_AWS_ACCOUNT_ID"
reddit_client_id  = "YOUR_REDDIT_CLIENT_ID"
reddit_secret     = "YOUR_REDDIT_CLIENT_SECRET"
```

### 3. Apply infrastructure

```bash
terraform apply
```

This will provision:
- VPC, Subnets, ECS Cluster (Fargate)
- MSK (Kafka), RDS (PostgreSQL), IAM Roles
- Secrets Manager for Reddit and DB creds

### 4. Deploy containers

After pushing Docker images to ECR (via CI/CD), ECS services will pull and run the containers.

---

## 📊 Monitoring

- Logs are automatically sent to **AWS CloudWatch Logs**
- You can monitor ECS container status, memory/CPU, and task logs in the AWS Console.

---

## 📎 License

MIT

---

## 🙌 Acknowledgements

- Reddit API
- Streamlit
- Terraform AWS modules
- Kafka & Airflow OSS communities

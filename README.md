# Task Manager API - DevOps SRE Project

A cloud-native Task Manager REST API demonstrating modern DevOps and SRE practices.

## Live URLs

| Service | URL |
|---------|-----|
| **Jenkins CI/CD** | http://54.81.96.179:8080 |
| **SonarQube** | http://54.81.96.179:9000 |

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | FastAPI (Python 3.11) |
| **Database** | PostgreSQL (AWS RDS) / SQLite (local) |
| **Containerization** | Docker (multi-stage builds) |
| **Orchestration** | Kubernetes (AWS EKS) |
| **CI/CD** | Jenkins Pipeline |
| **Infrastructure** | Terraform |
| **Code Quality** | SonarQube |
| **Security Scanning** | Trivy (containers), Safety (dependencies) |
| **Monitoring** | AWS CloudWatch |

## Project Structure

```
├── app/                    # Application source code
│   ├── main.py            # FastAPI application entry point
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── crud.py            # Database CRUD operations
│   ├── database.py        # Database configuration
│   └── logger.py          # CloudWatch logging setup
├── tests/                  # Test suite
│   ├── conftest.py        # Pytest fixtures
│   └── test_api.py        # API endpoint tests
├── kubernetes/            # Kubernetes manifests
│   ├── deployment.yaml    # Application deployment
│   ├── service.yaml       # LoadBalancer service
│   ├── hpa.yaml           # Horizontal Pod Autoscaler
│   └── secrets.yaml       # Secrets template
├── terraform/             # Infrastructure as Code
│   ├── main.tf            # Provider configuration
│   ├── variables.tf       # Input variables
│   ├── vpc.tf             # VPC and networking
│   ├── eks.tf             # EKS cluster
│   ├── ecr.tf             # Container registry
│   ├── rds.tf             # PostgreSQL database
│   └── outputs.tf         # Terraform outputs
├── Dockerfile             # Multi-stage Docker build
├── Jenkinsfile            # CI/CD pipeline definition
├── sonar-project.properties  # SonarQube configuration
└── requirements.txt       # Python dependencies
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint |
| `GET` | `/health` | Health check |
| `GET` | `/ready` | Readiness check |
| `GET` | `/api/tasks/` | List all tasks (with filters) |
| `POST` | `/api/tasks/` | Create a new task |
| `GET` | `/api/tasks/{id}` | Get task by ID |
| `PUT` | `/api/tasks/{id}` | Update a task |
| `DELETE` | `/api/tasks/{id}` | Delete a task |
| `GET` | `/api/tasks/stats/summary` | Get task statistics |

### Query Parameters

- `completed` (bool): Filter by completion status
- `priority` (string): Filter by priority (low, medium, high)

## Local Development

### Prerequisites

- Python 3.11+
- Docker (optional)

### Setup

```bash
# Clone the repository
git clone https://github.com/priyankakapoor12/DevOps-SRE-Project.git
cd Submission

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run the application
uvicorn app.main:app --reload

# Run tests
pytest tests/ -v --cov=app
```

### Docker

```bash
# Build image
docker build -t task-manager:latest .

# Run container
docker run -p 8000:8000 task-manager:latest
```

Access the API at `http://localhost:8000` and docs at `http://localhost:8000/docs`

## CI/CD Pipeline

The Jenkins pipeline includes the following stages:

```
┌─────────────┐    ┌─────────────────────┐    ┌───────────┐
│  Checkout   │───▶│ Install Dependencies│───▶│ Run Tests │
└─────────────┘    └─────────────────────┘    └─────┬─────┘
                                                    │
┌─────────────┐    ┌─────────────────────┐    ┌─────▼─────┐
│Quality Gate │◀───│  SonarQube Analysis │◀───│  Coverage │
└──────┬──────┘    └─────────────────────┘    └───────────┘
       │
┌──────▼──────┐    ┌─────────────────────┐    ┌───────────┐
│Security Scan│───▶│  Build Docker Image │───▶│Trivy Scan │
└─────────────┘    └─────────────────────┘    └─────┬─────┘
                                                    │
┌─────────────┐    ┌─────────────────────┐    ┌─────▼─────┐
│   Verify    │◀───│   Deploy to EKS     │◀───│Push to ECR│
└─────────────┘    └─────────────────────┘    └───────────┘
```

## Infrastructure (Terraform)

The Terraform configuration provisions:

- **VPC**: Multi-AZ setup with public/private subnets
- **EKS**: Managed Kubernetes cluster with node groups
- **ECR**: Container registry with lifecycle policies
- **RDS**: PostgreSQL database with encryption

```bash
cd terraform

# Initialize
terraform init

# Plan
terraform plan -var="db_username=admin" -var="db_password=<password>"

# Apply
terraform apply -var="db_username=admin" -var="db_password=<password>"
```

## Kubernetes Deployment

The application is deployed with:

- **2 replicas** (minimum) for high availability
- **Horizontal Pod Autoscaler** (2-3 pods based on CPU/memory)
- **Health checks** (liveness and readiness probes)
- **Resource limits** (CPU: 500m, Memory: 256Mi)
- **LoadBalancer service** for external access






## License

This project is part of an SRE assessment demonstration.

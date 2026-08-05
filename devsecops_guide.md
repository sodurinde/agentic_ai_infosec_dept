# DevSecOps Guide: Modular Agentic Banking Security Microservices

This DevSecOps guide outlines the phased development, testing, automation, and hybrid deployment (Google Cloud + Proxmox VE) of the 38 InfoSec agent microservices inside the Antigravity IDE (or Claude Code).

---

## Phase 0: Developer Environment & Baseline Setup
Before developing individual agents, the shared library and base template services must be verified.

### 1. Initialize Local Virtual Environment
Run the following commands in the workspace root directory:
```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Unix/macOS:
source venv/bin/activate

# Install baseline dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
ENVIRONMENT=development
PORT=8000
MONGO_URI=mongodb://localhost:27017
DB_NAME=bank_infosec
LOCAL_LOG_DIR=C:/Users/HP/.gemini/antigravity/scratch/bank_infosec_agent_stories/logs
GCP_PROJECT=bank-infosec-dev
GCS_BUCKET=bank-audit-logs-dev
PARQUET_LOG_BUFFER_SIZE=5
PARQUET_ARCHIVE_INTERVAL_SECONDS=10
```

### 3. Start Local Database and Baseline Service
Use docker-compose to launch a local MongoDB instance and rebuild the base template service:
```powershell
# Build and run infrastructure
docker-compose up -d --build

# Verify MongoDB and base service container statuses
docker-compose ps
```

---

## Phase 1: Incremental Agent Service Plugin (Multiple Developers)
When a developer is assigned one of the 38 agent stories, they follow this workflow:

### 1. Code Branching Strategy
```powershell
# Create feature branch corresponding to agent story ID (e.g. Story 5: SOC Agent)
git checkout -b feature/story-5-soc-agent
```

### 2. Copy Base Service Template
```powershell
# Copy base service to new service folder
Copy-Item -Path "services/base_service" -Destination "services/soc_service" -Recurse
```

### 3. Plugin Service Customizations
Within `services/soc_service/main.py`:
- Rename Beanie Document models to match the agent's requirements (e.g., `Alert`, `Playbook`).
- Implement the specific FastAPI routes listed in the Agent Story's Implementation Prompt.
- Update `services/soc_service/Dockerfile` to point to `services/soc_service/main.py`.
- Add the service under the `services` block of `docker-compose.yml` to enable multi-container local execution.

### 4. Running Local Tests
Create a test file `services/soc_service/test_soc.py` and run it locally:
```powershell
# Run service-specific pytest
pytest services/soc_service/
```

---

## Phase 2: Complete CI/CD Pipeline (GitHub Actions)
Create a `.github/workflows/ci-cd.yml` workflow file in the project root. This workflow triggers linting, security scans, unit tests, and builds container images on branch pushes and pulls.

```yaml
name: InfoSec Agents DevSecOps CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint-and-scan:
    name: Code Quality & Security Scanning
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install Dependencies
        run: |
          pip install flake8 black bandit
          pip install -r requirements.txt

      - name: Run Flake8 (Linting)
        run: flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

      - name: Run Black (Formatting Check)
        run: black --check .

      - name: Run Bandit (Python SAST Scan)
        run: bandit -r shared/ services/ -x **/*test*.py

  test:
    name: Unit & Integration Testing
    runs-on: ubuntu-latest
    needs: lint-and-scan
    services:
      mongodb:
        image: mongo:6.0
        ports:
          - 27017:27017
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: pip install -r requirements.txt

      - name: Run Tests
        env:
          MONGO_URI: mongodb://localhost:27017
          DB_NAME: test_db
          ENVIRONMENT: testing
          LOCAL_LOG_DIR: ./test_logs
          GCP_PROJECT: mock-project
          GCS_BUCKET: mock-bucket
        run: pytest

  build-and-push-gcp:
    name: Build & Push to GCP Artifact Registry
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    permissions:
      contents: 'read'
      id-token: 'write'
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      # Setup Workload Identity Federation (WIF) for secure keyless auth
      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'github-actions-sa@bank-infosec-prod.iam.gserviceaccount.com'

      - name: Setup Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker authentication for GCP Artifact Registry
        run: gcloud auth configure-docker us-central1-docker.pkg.dev

      # Building and pushing the base service template (repeat steps for each dynamic service folder)
      - name: Build and Push Base Service Container
        run: |
          docker build -t us-central1-docker.pkg.dev/bank-infosec-prod/agent-images/base-service:latest -f services/base_service/Dockerfile .
          docker push us-central1-docker.pkg.dev/bank-infosec-prod/agent-images/base-service:latest
```

---

## Phase 3: Deployment to Google Cloud (Sovereign Cloud Deployment)
Each microservice is deployed as an isolated service in **Google Cloud Run**, communicating with a managed MongoDB database (such as MongoDB Atlas on GCP) and archiving logs to **Google Cloud Storage (GCS)**.

### 1. Provision GCS Bucket for Parquet Logs
Ensure bucket lifecycle policy is configured to use Immutable Storage (WORM - Write Once Read Many) to comply with banking audits.
```powershell
# Create log storage bucket
gcloud storage buckets create gs://bank-audit-logs-prod --project=bank-infosec-prod --location=us-central1 --uniform-bucket-level-access

# Enable retention policy on bucket (WORM compliance for 7 years)
gcloud storage buckets update gs://bank-audit-logs-prod --retention-period=220752000s
```

### 2. Deploy Container to GCP Cloud Run
Deploying the microservice image using Cloud Run serverless endpoints:
```powershell
gcloud run deploy base-service `
  --image=us-central1-docker.pkg.dev/bank-infosec-prod/agent-images/base-service:latest `
  --region=us-central1 `
  --platform=managed `
  --allow-unauthenticated=false `
  --service-account=agent-runner-sa@bank-infosec-prod.iam.gserviceaccount.com `
  --set-env-vars="ENVIRONMENT=production,MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/prod_db,DB_NAME=prod_db,GCS_BUCKET=bank-audit-logs-prod" `
  --max-instances=10 `
  --concurrency=80
```

---

## Phase 4: Deployment to Proxmox VE (On-Premises Infrastructure)
For regulatory sovereignty, payment processing, or physical isolation, select agent services run on **Proxmox Virtual Environment (PVE)** inside Linux Containers (LXC) or Kernel-based Virtual Machines (KVM).

### 1. Provisioning Target LXC Container on Proxmox VE
You can execute CLI scripts on your PVE hypervisor node to spawn containers hosting microservices:
```bash
# Provision a Debian LXC container (ID 501) with Docker pre-installed
pct create 501 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  -ostemplate local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  -cores 2 -memory 2048 -swap 512 \
  -features nesting=1 \
  -net0 name=eth0,bridge=vmbr0,ip=192.168.1.150/24,gw=192.168.1.1 \
  -storage local-lvm -rootfs 20
```

### 2. Deployment Automation via Ansible Playbook
Create a deployment playbook `ansible/deploy-proxmox.yml` to automate updating the microservice on your Proxmox nodes.

```yaml
- name: Deploy InfoSec Microservices to Proxmox LXC Node
  hosts: proxmox_lxc_agents
  become: yes
  vars:
    project_dest: "/opt/bank_infosec"
  tasks:
    - name: Ensure target directory exists
      file:
        path: "{{ project_dest }}"
        state: directory
        owner: root
        group: root
        mode: '0755'

    - name: Copy project configuration files
      copy:
        src: ../docker-compose.yml
        dest: "{{ project_dest }}/docker-compose.yml"

    - name: Pull latest microservice containers from registry
      docker_image:
        name: "us-central1-docker.pkg.dev/bank-infosec-prod/agent-images/{{ item }}"
        source: pull
      loop:
        - "base-service"

    - name: Restart microservices via Docker Compose
      community.docker.docker_compose_v2:
        project_src: "{{ project_dest }}"
        state: restarted
        pull: always
```

Associated command to trigger the Proxmox local deploy:
```powershell
# Run the Ansible playbook targeting on-premises Proxmox node inventories
ansible-playbook -i ansible/hosts ansible/deploy-proxmox.yml
```

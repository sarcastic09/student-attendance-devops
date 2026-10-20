# Student Attendance System — End-to-End DevOps Mini-Project

A small Flask + SQLite attendance application used to demonstrate Git/GitHub, Pytest, Jenkins CI/CD, Docker, Docker Hub, Prometheus, Grafana, host metrics, and alert rules.

## Application features
- Add and delete students
- Mark Present/Absent attendance by date
- View daily attendance history
- Calculate each student's attendance percentage
- Health/readiness endpoints and Prometheus `/metrics`

## Run locally with Python
Requires Python 3.12 or a compatible recent Python.

```bash
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
$env:DATABASE_PATH = "attendance.db" # Windows PowerShell
python app.py
```

Open http://localhost:5000. For Linux/macOS, set `export DATABASE_PATH=./attendance.db` first.

## Run tests
```bash
pip install -r requirements.txt
pytest -v
```

## Run the full local stack
1. Copy `.env.example` to `.env`.
2. Set `DOCKERHUB_USERNAME` to your Docker Hub username if publishing; otherwise `localuser` is fine for local development.
3. Change `GRAFANA_ADMIN_PASSWORD` before sharing or exposing the stack.
4. Run `docker compose up -d --build`.
5. Open app http://localhost:5000, Prometheus http://localhost:9090, Grafana http://localhost:3000, Node Exporter http://localhost:9100, cAdvisor http://localhost:8085.
6. Stop with `docker compose down`; persistent data remains in Docker volumes. Use `docker compose down -v` only if you intentionally want to delete stored data/metrics.

## Jenkins configuration overview
- Jenkins needs Git, Python 3, Docker CLI + Compose plugin, and access to the host Docker socket.
- Configure a Pipeline job from the GitHub repository and use `Jenkinsfile`.
- Add a Jenkins username/password credential with ID `dockerhub-credentials`; username is your Docker Hub username and password is a Docker Hub access token.
- Set the Docker Hub username used by Compose in the Jenkins build environment when needed. The sample Jenkinsfile publishes on every successful run; for a real team project, restrict publishing/deployment to the protected `main` branch.
- For a real webhook-triggered pipeline, configure a GitHub webhook to `http(s)://YOUR-JENKINS-URL/github-webhook/` and enable the GitHub hook trigger in the job. Jenkins must be reachable by GitHub.

## Monitoring and alerts
Prometheus scrapes the app `/metrics`, Node Exporter, cAdvisor, and itself. Grafana provisions a Prometheus datasource and an overview dashboard. Alert rules cover application down and host CPU above 80% for five minutes. Prometheus evaluates these rules; configure Grafana contact points/notification policies to send email or another notification channel.

## Suggested Git workflow
```bash
git init
git add .
git commit -m "Initial student attendance application"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/student-attendance-devops.git
git push -u origin main
```

## Security notes
This is an educational local lab. Change default secrets, avoid exposing Jenkins/Docker socket to untrusted users, and do not expose the development services directly to the public internet. SQLite is appropriate for a small demo, not a multi-user production deployment.

## Start Jenkins in the Compose stack
The Compose stack includes a local Jenkins service on http://localhost:8080. On first startup, retrieve the initial administrator password with:

```bash
docker exec attendance-jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

Complete the setup wizard, install suggested plugins (the `Jenkinsfile` also uses Pipeline, Git, Credentials Binding, and Workspace Cleanup functionality), and create a Pipeline job configured as **Pipeline script from SCM**, Git, with your GitHub repository URL and script path `Jenkinsfile`. Add a Jenkins credential of type **Username with password**, ID `dockerhub-credentials`, username your Docker Hub username, password a Docker Hub access token. For the initial test you can run the pipeline manually; webhook delivery requires a Jenkins URL reachable from GitHub.

**Docker socket warning:** mounting `/var/run/docker.sock` gives Jenkins control over the host Docker daemon and effectively high host privileges. Use this only in a trusted local lab, never for an untrusted multi-user Jenkins server.

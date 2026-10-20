pipeline {
  agent any
  options { timestamps(); disableConcurrentBuilds() }
  environment {
    COMPOSE_PROJECT_NAME = 'student-attendance'
    IMAGE_NAME = 'student-attendance'
  }
  stages {
    stage('Checkout') {
      steps { checkout scm; sh 'git rev-parse --short HEAD' }
    }
    stage('Install Dependencies') {
      steps { sh 'python3 -m venv .venv && . .venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt' }
    }
    stage('Build / Validate') {
      steps { sh '. .venv/bin/activate && python3 -m compileall -q app.py tests && test -f Dockerfile && test -f docker-compose.yml' }
    }
    stage('Automated Tests') {
      steps { sh '. .venv/bin/activate && pytest -v' }
    }
    stage('Docker Build') {
      steps { sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest .' }
    }
    stage('Docker Hub Push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          sh '''set +x
            echo "$DOCKERHUB_TOKEN" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin
            docker tag ${IMAGE_NAME}:${BUILD_NUMBER} "$DOCKERHUB_USERNAME/${IMAGE_NAME}:${BUILD_NUMBER}"
            docker tag ${IMAGE_NAME}:${BUILD_NUMBER} "$DOCKERHUB_USERNAME/${IMAGE_NAME}:latest"
            docker push "$DOCKERHUB_USERNAME/${IMAGE_NAME}:${BUILD_NUMBER}"
            docker push "$DOCKERHUB_USERNAME/${IMAGE_NAME}:latest"
            docker logout
          '''
        }
      }
    }
    stage('Deploy') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'dockerhub-credentials', usernameVariable: 'DOCKERHUB_USERNAME', passwordVariable: 'DOCKERHUB_TOKEN')]) {
          sh '''
            docker compose pull app
            docker compose up -d --no-build app
            sleep 5
            python3 -c "import urllib.request; print(urllib.request.urlopen('http://host.docker.internal:5000/health', timeout=10).read().decode())"
          '''
        }
      }
    }
  }
  post {
    always { sh 'docker image prune -f || true'; cleanWs() }
    success { echo 'Pipeline passed: tests, Docker build, and configured deployment stages completed.' }
    failure { echo 'Pipeline failed. Review the stage logs; deployment must not proceed after a test failure.' }
  }
}

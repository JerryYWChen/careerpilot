# Cloud and Container Project Foundations

This sample note describes practical ways to build evidence for cloud and container skills. It is intentionally general and should be replaced or supplemented with curated, attributed sources before the knowledge base is used for production recommendations.

## Container fundamentals

A useful first container project starts with an application that already runs locally. Add a Dockerfile that installs only the required dependencies, copies the application code, exposes the application port, and defines a clear startup command. Add a compose file only when the project genuinely needs multiple services, such as an API and a database. The evidence should show that the candidate can build the image, run the container, pass configuration through environment variables, inspect logs, and explain the difference between build-time and runtime configuration.

The project becomes stronger when it includes a health check, a non-root runtime user, a small image, and a short troubleshooting guide. These additions are useful because they demonstrate operating knowledge rather than merely listing Docker as a skill. A concise README should explain how to build, run, test, and stop the application. It should also record one or two problems encountered during containerization and how they were resolved.

## Orchestration progression

Container experience alone does not demonstrate orchestration experience. A reasonable Kubernetes learning step is to deploy the existing containerized application to a local cluster. Begin with a Deployment and Service, then add configuration and secrets without embedding sensitive values in source control. Show how replicas are updated, how failed pods are diagnosed, and how readiness and liveness checks affect traffic. Keep the first deployment small enough that each object has a clear purpose.

A portfolio project should avoid adding an ingress controller, service mesh, autoscaling, and observability stack all at once. Add infrastructure only when it supports a specific learning objective. Strong evidence includes manifests or a small Helm chart, repeatable setup instructions, and a brief explanation of tradeoffs. The goal is to show that the candidate understands scheduling, service discovery, configuration, rollout behavior, and basic debugging - not that the project imitates a large production platform.

## Cloud deployment

Cloud evidence is clearest when the candidate can connect a service to a concrete deployment workflow. A small project might publish a container image, deploy it to a managed runtime, configure permissions narrowly, and expose logs needed for troubleshooting. The documentation should identify which cloud services were used and why. It should separate cloud-provider knowledge from general container knowledge instead of treating one as proof of the other.

Cost and cleanup matter in learning projects. Prefer resources that can be removed predictably, document the cleanup command, and avoid leaving long-running infrastructure enabled. If infrastructure is defined as code, keep the first version small and reviewable. Useful evidence includes a deployment diagram, reproducible commands, a description of identity and access decisions, and confirmation that secrets are supplied through an appropriate configuration mechanism.

6. Interview preparation
Why did you implement a health endpoint?
I implemented a lightweight liveness endpoint to verify that the application is operational. It provides a foundation for infrastructure monitoring, container health checks and automated deployment validation. I kept it independent of external dependencies so that application liveness can be distinguished from dependency readiness.

Why FastAPI instead of Flask?
FastAPI provides typed request and response validation, automatic OpenAPI documentation and asynchronous request-handling capabilities. These are useful for an AI application that communicates with external APIs and LLM providers.

Why separate routes and schemas?
Separating HTTP routing from response contracts improves maintainability and allows the API to evolve without mixing transport logic with business logic.
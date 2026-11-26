//This defines the frontend equivalent of our Pydantic response schema.
//
//It provides compile-time type checking in TypeScript. Unlike Pydantic, however, a TypeScript interface does not perform runtime validation.

export interface HealthResponse {
  service: string
  status: 'healthy'
  version: string
}
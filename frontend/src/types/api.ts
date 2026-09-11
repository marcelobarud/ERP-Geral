export type HealthResponse = {
  status: string
  process?: string
  database?: string
  schema?: string
  current_migration?: string | null
  expected_migration?: string | null
}

export type ApiErrorPayload = {
  detail?: string
}

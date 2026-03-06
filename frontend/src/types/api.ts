/** Generic API response wrapper — mirrors backend Response[T] */
export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

/** Paginated response — mirrors backend PaginatedResponse[T] */
export interface PaginatedResponse<T> {
  code: number
  message: string
  data: T[]
  total: number
  current: number
  pageSize: number
}

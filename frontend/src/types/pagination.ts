export type PaginationMeta = {
  page: number
  page_size: number
  total: number
  total_pages: number
}

export type PaginatedItems<T> = T[] & Partial<PaginationMeta>

export type PaginatedResponse<T> = PaginationMeta & {
  items: T[]
}

export const emptyPagination: PaginationMeta = {
  page: 1,
  page_size: 20,
  total: 0,
  total_pages: 0,
}

export function getPaginationMeta<T>(items: T[]): PaginationMeta {
  const paginated = items as PaginatedItems<T>
  return {
    page: paginated.page ?? 1,
    page_size: paginated.page_size ?? Math.max(items.length, 1),
    total: paginated.total ?? items.length,
    total_pages: paginated.total_pages ?? (items.length ? 1 : 0),
  }
}

export function attachPagination<T>(
  items: T[],
  meta: PaginationMeta,
): PaginatedItems<T> {
  const result = items as PaginatedItems<T>
  for (const [key, value] of Object.entries(meta)) {
    Object.defineProperty(result, key, {
      configurable: true,
      enumerable: false,
      value,
      writable: true,
    })
  }
  return result
}

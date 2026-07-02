/**
 * usePagination — generic client-side pagination hook.
 *
 * @example
 *   const { page, pageSize, offset, goTo, next, prev, pageCount } =
 *     usePagination({ total: items.length, pageSize: 20 })
 *   const visible = items.slice(offset, offset + pageSize)
 */
import { useState } from 'react'

interface UsePaginationOptions {
  /** Total number of items */
  total: number
  /** Items per page (default: 20) */
  pageSize?: number
  /** Initial page, 1-indexed (default: 1) */
  initialPage?: number
}

export function usePagination({
  total,
  pageSize = 20,
  initialPage = 1,
}: UsePaginationOptions) {
  const [page, setPage] = useState(initialPage)

  const pageCount = Math.max(1, Math.ceil(total / pageSize))
  const safePage  = Math.min(Math.max(1, page), pageCount)
  const offset    = (safePage - 1) * pageSize

  function goTo(p: number) {
    setPage(Math.min(Math.max(1, p), pageCount))
  }

  function next() {
    goTo(safePage + 1)
  }

  function prev() {
    goTo(safePage - 1)
  }

  function reset() {
    setPage(initialPage)
  }

  return {
    /** Current page (1-indexed) */
    page: safePage,
    /** Number of items per page */
    pageSize,
    /** Slice offset: `items.slice(offset, offset + pageSize)` */
    offset,
    /** Total page count */
    pageCount,
    /** True if there is a next page */
    hasNext: safePage < pageCount,
    /** True if there is a previous page */
    hasPrev: safePage > 1,
    /** Navigate to a specific page (1-indexed) */
    goTo,
    /** Navigate to next page */
    next,
    /** Navigate to previous page */
    prev,
    /** Reset to initial page */
    reset,
  }
}

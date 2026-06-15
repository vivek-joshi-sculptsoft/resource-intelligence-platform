import { useState } from 'react'
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table'
import type { PaginationMeta } from '../types/api'

interface DataTableProps<T> {
  columns: ColumnDef<T, unknown>[]
  data: T[]
  meta?: PaginationMeta | null
  page?: number
  onPageChange?: (page: number) => void
  onRowClick?: (row: T) => void
  isLoading?: boolean
  emptyIcon?: string
  emptyTitle?: string
  emptyDescription?: string
  emptyAction?: React.ReactNode
}

export function DataTable<T>({
  columns,
  data,
  meta,
  page = 1,
  onPageChange,
  onRowClick,
  isLoading = false,
  emptyIcon = '\u{1F4CB}',
  emptyTitle = 'No data found',
  emptyDescription = 'Try adjusting your filters.',
  emptyAction,
}: DataTableProps<T>) {
  const [sorting, setSorting] = useState<SortingState>([])

  const table = useReactTable({
    data,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  })

  if (isLoading) {
    return (
      <div
        className="flex items-center justify-center rounded-xl py-20"
        style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        <div className="flex items-center gap-3 text-[14px]" style={{ color: '#7C85C0' }}>
          <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Loading...
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div
        className="flex flex-col items-center justify-center rounded-xl py-20 text-center"
        style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
      >
        <div className="mb-4 text-[56px] opacity-70">{emptyIcon}</div>
        <div className="mb-1.5 text-[18px] font-semibold" style={{ color: '#1e1b4b' }}>
          {emptyTitle}
        </div>
        <div className="mb-6 text-[14px]" style={{ color: '#6b7280' }}>
          {emptyDescription}
        </div>
        {emptyAction}
      </div>
    )
  }

  return (
    <div
      className="overflow-hidden rounded-xl"
      style={{ background: '#fff', boxShadow: '0 2px 8px rgba(43,57,144,0.06), 0 1px 3px rgba(0,0,0,0.04)' }}
    >
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-[13.5px]">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className={`whitespace-nowrap px-4 py-[13px] text-[12.5px] font-semibold uppercase tracking-wide text-white first:pl-5 last:pr-5 ${
                      header.column.getCanSort() ? 'cursor-pointer select-none' : ''
                    }`}
                    style={{
                      background: 'linear-gradient(135deg, #2B3990, #4A5BB5)',
                      letterSpacing: '0.3px',
                    }}
                    onClick={header.column.getToggleSortingHandler()}
                  >
                    <div className="flex items-center gap-1.5">
                      {header.isPlaceholder
                        ? null
                        : flexRender(header.column.columnDef.header, header.getContext())}
                      {header.column.getIsSorted() === 'asc' && (
                        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="18 15 12 9 6 15" />
                        </svg>
                      )}
                      {header.column.getIsSorted() === 'desc' && (
                        <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                          <polyline points="6 9 12 15 18 9" />
                        </svg>
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row, idx) => (
              <tr
                key={row.id}
                className={`transition-colors ${onRowClick ? 'cursor-pointer' : ''}`}
                style={{ borderBottom: '1px solid #E8EAF6', background: idx % 2 === 1 ? '#F5F6FC' : '#fff' }}
                onClick={() => onRowClick?.(row.original)}
                onMouseEnter={(e) => {
                  if (onRowClick) (e.currentTarget as HTMLElement).style.background = '#E8EAF6'
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.background = idx % 2 === 1 ? '#F5F6FC' : '#fff'
                }}
              >
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="whitespace-nowrap px-4 py-[13px] first:pl-5 last:pr-5"
                    style={{ color: '#1e1b4b' }}
                  >
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {meta && onPageChange && (
        <div
          className="flex items-center justify-between px-5 py-3.5"
          style={{ borderTop: '1px solid #E8EAF6' }}
        >
          <span className="text-[13px]" style={{ color: '#6b7280' }}>
            Showing {(meta.page - 1) * meta.limit + 1}&ndash;
            {Math.min(meta.page * meta.limit, meta.total)} of {meta.total}
          </span>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="rounded-md px-4 py-1.5 text-[13px] font-medium transition-all disabled:cursor-not-allowed disabled:opacity-40"
              style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}
            >
              Prev
            </button>
            <button
              disabled={page >= meta.total_pages}
              onClick={() => onPageChange(page + 1)}
              className="rounded-md px-4 py-1.5 text-[13px] font-medium transition-all disabled:cursor-not-allowed disabled:opacity-40"
              style={{ border: '1px solid #D6DAF0', background: '#fff', color: '#6b7280' }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

import { useMemo, useState } from "react";
import "./DataTable.css";

const PAGE_SIZE = 50;

/**
 * Generic paginated table for arrays of row objects. Used for pending_rows,
 * qc_errors lists, duplicate_ali.duplicate_rows, etc - all of which can be
 * hundreds/thousands of rows, so we paginate client-side rather than
 * rendering everything at once.
 */
export default function DataTable({ rows, emptyMessage = "No records." }) {
  const [page, setPage] = useState(0);

  const columns = useMemo(() => {
    if (!rows || rows.length === 0) return [];
    return Object.keys(rows[0]);
  }, [rows]);

  if (!rows || rows.length === 0) {
    return <p className="data-table-empty">{emptyMessage}</p>;
  }

  const totalPages = Math.ceil(rows.length / PAGE_SIZE);
  const start = page * PAGE_SIZE;
  const pageRows = rows.slice(start, start + PAGE_SIZE);

  return (
    <div className="data-table-wrap">
      <div className="data-table-scroll">
        <table className="data-table">
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col}>{col}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageRows.map((row, i) => (
              <tr key={start + i}>
                {columns.map((col) => (
                  <td key={col}>{formatCell(row[col])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {totalPages > 1 && (
        <div className="data-table-pagination">
          <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            ← Prev
          </button>
          <span>
            Page {page + 1} of {totalPages} ({rows.length} rows)
          </span>
          <button disabled={page >= totalPages - 1} onClick={() => setPage((p) => p + 1)}>
            Next →
          </button>
        </div>
      )}
    </div>
  );
}

function formatCell(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

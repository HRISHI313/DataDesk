import SummaryCards from "./SummaryCards";
import PctBreakdown from "./PctBreakdown";
import DataTable from "./DataTable";
import CollapsibleSection from "./CollapsibleSection";
import "./ResultsDashboard.css";

export default function ResultsDashboard({ results }) {
  const {
    per_retailer,
    construction_flag,
    construction_pct,
    polygon_status,
    polygon_pct,
    duplicate_ali,
    parent_ali,
    qc_errors,
    polygon_coverage,
  } = results;

  const hasQcErrors = qc_errors.total_errors > 0;
  const hasDuplicates = duplicate_ali.duplicate_count > 0;

  return (
    <div className="results-dashboard">
      <SummaryCards results={results} />

      <div className="dashboard-grid">
        <section className="dashboard-panel">
          <h3>Records per retailer</h3>
          <DataTable rows={per_retailer} />
        </section>

        <section className="dashboard-panel">
          <h3>Verification status</h3>
          <PctBreakdown data={polygon_pct} />
        </section>
      </div>

      <div className="dashboard-grid">
        <section className="dashboard-panel">
          <h3>Location type breakdown</h3>
          <PctBreakdown data={construction_pct} />
        </section>

        <section className="dashboard-panel">
          <h3>Parent ALI linkage</h3>
          <PctBreakdown
            data={{
              Connected: parent_ali.connected,
              Unknown: parent_ali.unknown,
            }}
          />
        </section>
      </div>

      <section className="dashboard-panel">
        <h3>Polygon status by retailer</h3>
        <DataTable rows={polygon_status} />
      </section>

      <section className="dashboard-panel">
        <h3>Location type by retailer</h3>
        <DataTable rows={construction_flag} />
      </section>

      <section className="dashboard-panel">
        <h3>Parent ALI by retailer</h3>
        <DataTable rows={parent_ali.per_retailer} />
      </section>

      <CollapsibleSection
        title="QC Errors"
        badge={qc_errors.total_errors}
        badgeTone={hasQcErrors ? "bad" : "good"}
        defaultOpen={hasQcErrors}
      >
        {!hasQcErrors && <p className="dashboard-clean-msg">No QC errors found.</p>}
        {qc_errors.mall_tenant_errors.length > 0 && (
          <>
            <h4>Mall Tenant records with a Polygon Status set (should be empty)</h4>
            <DataTable rows={qc_errors.mall_tenant_errors} />
          </>
        )}
        {qc_errors.multi_level_errors.length > 0 && (
          <>
            <h4>Multi-Level records with a Polygon Status set (should be empty)</h4>
            <DataTable rows={qc_errors.multi_level_errors} />
          </>
        )}
        {qc_errors.construction_errors.length > 0 && (
          <>
            <h4>Construction record errors</h4>
            <DataTable rows={qc_errors.construction_errors} />
          </>
        )}
      </CollapsibleSection>

      <CollapsibleSection
        title="Duplicate ALIs"
        badge={duplicate_ali.duplicate_count}
        badgeTone={hasDuplicates ? "warn" : "good"}
      >
        {!hasDuplicates && <p className="dashboard-clean-msg">No duplicate ALIs found.</p>}
        {hasDuplicates && <DataTable rows={duplicate_ali.duplicate_rows} />}
      </CollapsibleSection>

      <CollapsibleSection
        title="Pending records"
        badge={polygon_coverage.pending_count}
        badgeTone="warn"
      >
        <p className="dashboard-hint">
          Records with no Polygon Status and not Mall Tenant/Multi-Level - these need drawing.
        </p>
        <DataTable rows={polygon_coverage.pending_rows} />
      </CollapsibleSection>
    </div>
  );
}

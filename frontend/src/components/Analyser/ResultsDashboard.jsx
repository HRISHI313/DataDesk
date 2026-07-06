import SummaryCards from "./SummaryCards";
import PctBreakdown from "./PctBreakdown";
import DataTable from "./DataTable";
import CollapsibleSection from "./CollapsibleSection";
import LaunchTaskBar from "./LaunchTaskBar";
import "./ResultsDashboard.css";

export default function ResultsDashboard({ results, uploadId, onLaunchTask }) {
  const {
    per_retailer,
    construction_flag,
    construction_pct,
    polygon_status,
    polygon_pct,
    duplicate_ali,
    parent_ali,
    qc_errors,
  } = results;

  const hasQcErrors = qc_errors.total_errors > 0;
  const hasDuplicates = duplicate_ali.duplicate_count > 0;

  return (
    <div className="results-dashboard">
      <SummaryCards results={results} />

      <LaunchTaskBar uploadId={uploadId} onLaunchTask={onLaunchTask} />

      {/* QC Errors first - the actionable "fix this" signal, so it's the
          first thing an analyst sees, not buried at the bottom. */}
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
            <h4>Construction records that look already completed</h4>
            <p className="dashboard-hint">
              Has a Polygon Status set, or Geo Accuracy already shows a verified rooftop pin -
              shouldn't happen for a site still under construction.
            </p>
            <DataTable rows={qc_errors.construction_errors} />
          </>
        )}
      </CollapsibleSection>

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
          <h3>Geofencing type breakdown</h3>
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
        <h3>Geofencing type by retailer</h3>
        <DataTable rows={construction_flag} />
      </section>

      <section className="dashboard-panel">
        <h3>Parent ALI by retailer</h3>
        <DataTable rows={parent_ali.per_retailer} />
      </section>

      <CollapsibleSection
        title="Duplicate ALIs"
        badge={duplicate_ali.duplicate_count}
        badgeTone={hasDuplicates ? "warn" : "good"}
      >
        {!hasDuplicates && <p className="dashboard-clean-msg">No duplicate ALIs found.</p>}
        {hasDuplicates && <DataTable rows={duplicate_ali.duplicate_rows} />}
      </CollapsibleSection>
    </div>
  );
}

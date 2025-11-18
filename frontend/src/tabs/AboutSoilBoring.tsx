export default function AboutSoilBoring() {
  return (
    <div className="card" style={{ lineHeight: 1.6 }}>
      <h2>Why Soil Boring Matters</h2>
      <p>
        Soil boring is a critical pre-construction activity for gathering technical and geotechnical data about a site.
        The highlights below are derived from the project specification document (<code>soilboring.md</code>).
      </p>

      <h3>Key Objectives</h3>
      <ol>
        <li>
          <strong>Determine Soil Characteristics:</strong> Identify soil type (clay, sand, silt, gravel), moisture content,
          density, and strength parameters to quantify bearing capacity.
        </li>
        <li>
          <strong>Assess Stability &amp; Bearing Capacity:</strong> Evaluate whether the ground can safely support the planned
          structures to prevent settlement, lateral movement, or failure.
        </li>
        <li>
          <strong>Select Foundation Type:</strong> Findings guide the decision between shallow footings, deep piles, or other
          foundation systems, including their depth and sizing.
        </li>
        <li>
          <strong>Identify Geotechnical Risks:</strong> Detect soft/expansive layers, high groundwater, contamination, or
          difficult bedrock horizons that could threaten constructability.
        </li>
        <li>
          <strong>Support Planning &amp; Costing:</strong> Accurate subsurface knowledge allows realistic construction methods,
          schedules, and budgets before mobilization.
        </li>
      </ol>

      <h3>How This App Helps</h3>
      <ul>
        <li>Centralizes borehole logs with groundwater, USCS, and SPT metrics.</li>
        <li>Surfaces method and soil-class distributions for quick stability insight.</li>
        <li>Provides AI-assisted narratives to brief stakeholders on risks and design drivers.</li>
        <li>Maintains searchable CSV exports for downstream geotechnical analysis.</li>
      </ul>
    </div>
  )
}

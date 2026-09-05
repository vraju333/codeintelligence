let discoveredEndpoints = [];


document.addEventListener(
    "DOMContentLoaded",
    async () => {

        checkHealth();
        loadScenarios();

        document
            .getElementById("flowMethod")
            .addEventListener(
                "change",
                () => {
                    refreshEndpointDropdown(
                        "flowMethod",
                        "flowEndpoint"
                    );
                }
            );

        document
            .getElementById("chartMethod")
            .addEventListener(
                "change",
                () => {
                    refreshEndpointDropdown(
                        "chartMethod",
                        "chartEndpoint"
                    );
                }
            );

        document
            .getElementById("investigationMethod")
            .addEventListener(
                "change",
                () => {
                    refreshEndpointDropdown(
                        "investigationMethod",
                        "investigationEndpoint"
                    );
                }
            );

        await loadProjectEndpoints();
    }
);


async function loadProjectEndpoints() {

    try {

        const response =
            await fetch(
                "/api/endpoint-flow/endpoints"
            );

        const data =
            await response.json();

        if (!response.ok) {
            throw new Error(
                JSON.stringify(data)
            );
        }

        if (Array.isArray(data)) {

            discoveredEndpoints =
                data;

        } else if (
            Array.isArray(
                data.endpoints
            )
        ) {

            discoveredEndpoints =
                data.endpoints;

        } else {

            discoveredEndpoints =
                [];
        }

        refreshEndpointDropdown(
            "flowMethod",
            "flowEndpoint"
        );

        refreshEndpointDropdown(
            "chartMethod",
            "chartEndpoint"
        );

        refreshEndpointDropdown(
            "investigationMethod",
            "investigationEndpoint"
        );

    } catch (error) {

        console.error(
            "Failed to load endpoints",
            error
        );

        showEndpointLoadError(
            "flowEndpoint"
        );

        showEndpointLoadError(
            "chartEndpoint"
        );

        showEndpointLoadError(
            "investigationEndpoint"
        );
    }
}


function refreshEndpointDropdown(
    methodElementId,
    endpointElementId
) {

    const methodElement =
        document.getElementById(
            methodElementId
        );

    const endpointSelect =
        document.getElementById(
            endpointElementId
        );

    if (
        !methodElement ||
        !endpointSelect
    ) {
        return;
    }

    const selectedMethod =
        String(
            methodElement.value
        ).toUpperCase();

    const matchingEndpoints =
        discoveredEndpoints
            .filter(
                item => {

                    const method =
                        String(
                            item.http_method
                            ||
                            item.httpMethod
                            ||
                            item.method
                            ||
                            item.request_method
                            ||
                            ""
                        ).toUpperCase();

                    return (
                        method ===
                        selectedMethod
                    );
                }
            )
            .sort(
                (
                    first,
                    second
                ) => {

                    return getEndpointPath(
                        first
                    ).localeCompare(
                        getEndpointPath(
                            second
                        )
                    );
                }
            );

    endpointSelect.innerHTML =
        "";

    if (
        matchingEndpoints.length ===
        0
    ) {

        const option =
            document.createElement(
                "option"
            );

        option.value =
            "";

        option.textContent =
            "No "
            + selectedMethod
            + " endpoints found";

        endpointSelect.appendChild(
            option
        );

        return;
    }

    for (
        const item
        of matchingEndpoints
    ) {

        const endpoint =
            getEndpointPath(
                item
            );

        if (!endpoint) {
            continue;
        }

        const controller =
            item.controller
            || {};

        const controllerClass =
            item.controller_class
            ||
            item.controllerClass
            ||
            item.class_name
            ||
            controller.class_name
            ||
            controller.className
            ||
            "";

        const controllerMethod =
            item.controller_method
            ||
            item.controllerMethod
            ||
            item.method_name
            ||
            controller.method_name
            ||
            controller.methodName
            ||
            "";

        const option =
            document.createElement(
                "option"
            );

        option.value =
            endpoint;

        if (
            controllerClass &&
            controllerMethod
        ) {

            option.textContent =
                endpoint
                + " — "
                + controllerClass
                + "."
                + controllerMethod;

        } else {

            option.textContent =
                endpoint;
        }

        endpointSelect.appendChild(
            option
        );
    }
}


function getEndpointPath(
    item
) {

    return (
        item.endpoint
        ||
        item.path
        ||
        item.url
        ||
        item.request_path
        ||
        ""
    );
}


function showEndpointLoadError(
    endpointElementId
) {

    const endpointSelect =
        document.getElementById(
            endpointElementId
        );

    if (!endpointSelect) {
        return;
    }

    endpointSelect.innerHTML =
        "";

    const option =
        document.createElement(
            "option"
        );

    option.value =
        "";

    option.textContent =
        "Unable to load endpoints";

    endpointSelect.appendChild(
        option
    );
}


async function checkHealth() {

    const element =
        document.getElementById(
            "healthStatus"
        );

    try {

        const response =
            await fetch(
                "/health"
            );

        if (!response.ok) {
            throw new Error(
                "Health check failed"
            );
        }

        element.textContent =
            "Backend Online";

        element.className =
            "status-badge status-success";

    } catch (error) {

        element.textContent =
            "Backend Offline";

        element.className =
            "status-badge status-error";
    }
}


async function loadScenarios() {

    const container =
        document.getElementById(
            "scenarioList"
        );

    container.innerHTML =
        "Loading...";

    try {

        const response =
            await fetch(
                "/api/scenarios"
            );

        const scenarios =
            await response.json();

        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    scenarios
                )
            );
        }

        if (
            !Array.isArray(
                scenarios
            )
            ||
            scenarios.length === 0
        ) {

            container.innerHTML =
                "No scenarios found.";

            return;
        }

        container.innerHTML =
            scenarios
                .map(
                    scenario => `
                        <div class="scenario">

                            <div class="method">

                                ${escapeHtml(
                                    scenario.http_method
                                )}

                            </div>

                            <div>

                                <strong>

                                    ${escapeHtml(
                                        scenario.scenario_code
                                    )}

                                </strong>

                                <div>

                                    ${escapeHtml(
                                        scenario.scenario_name
                                        || ""
                                    )}

                                </div>

                            </div>

                            <div class="endpoint">

                                ${escapeHtml(
                                    scenario.endpoint
                                )}

                            </div>

                            <div>

                                <span class="tag">

                                    ${escapeHtml(
                                        scenario.status
                                        || "ACTIVE"
                                    )}

                                </span>

                            </div>

                        </div>
                    `
                )
                .join("");

    } catch (error) {

        container.innerHTML =
            renderError(
                error.message
            );
    }
}


async function analyseEndpointFlow() {

    const method =
        document.getElementById(
            "flowMethod"
        ).value;

    const endpoint =
        document.getElementById(
            "flowEndpoint"
        ).value;

    const container =
        document.getElementById(
            "flowResult"
        );

    if (!endpoint) {

        container.innerHTML =
            renderError(
                "Please select an endpoint."
            );

        return;
    }

    container.innerHTML =
        "Analysing...";

    try {

        const url =
            "/api/endpoint-flow/analyze"
            + "?http_method="
            + encodeURIComponent(
                method
            )
            + "&endpoint="
            + encodeURIComponent(
                endpoint
            );

        const response =
            await fetch(
                url
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    data
                )
            );
        }

        const flow =
            data.simplified_flow
            || [];

        if (
            flow.length === 0
        ) {

            container.innerHTML =
                "<pre>"
                +
                escapeHtml(
                    JSON.stringify(
                        data,
                        null,
                        2
                    )
                )
                +
                "</pre>";

            return;
        }

        container.innerHTML =
            `
            <div class="flow-list">

                ${
                    flow
                        .map(
                            (
                                step,
                                index
                            ) => {

                                const arrow =
                                    index ===
                                    flow.length - 1
                                    ? ""
                                    : `
                                        <div class="flow-arrow">
                                            ↓
                                        </div>
                                    `;

                                return `
                                    <div class="flow-step">

                                        ${escapeHtml(
                                            step
                                        )}

                                    </div>

                                    ${arrow}
                                `;
                            }
                        )
                        .join("")
                }

            </div>
            `;

    } catch (error) {

        container.innerHTML =
            renderError(
                error.message
            );
    }
}


async function runInvestigation() {

    const method =
        document.getElementById(
            "investigationMethod"
        ).value;

    const endpoint =
        document.getElementById(
            "investigationEndpoint"
        ).value;

    const container =
        document.getElementById(
            "investigationResult"
        );

    if (!endpoint) {

        container.innerHTML =
            renderError(
                "Please select an endpoint."
            );

        return;
    }

    let expected;
    let actual;

    try {

        expected =
            JSON.parse(
                document.getElementById(
                    "expectedJson"
                ).value
            );

        actual =
            JSON.parse(
                document.getElementById(
                    "actualJson"
                ).value
            );

    } catch (error) {

        container.innerHTML =
            renderError(
                "Expected or Actual JSON is invalid."
            );

        return;
    }

    container.innerHTML =
        "Running LangGraph investigation...";

    try {

        const url =
            "/api/investigation/analyse"
            + "?http_method="
            + encodeURIComponent(
                method
            )
            + "&endpoint="
            + encodeURIComponent(
                endpoint
            );

        const response =
            await fetch(
                url,
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(
                            {
                                expected:
                                    expected,

                                actual:
                                    actual
                            }
                        )
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    data
                )
            );
        }

        container.innerHTML =
            renderInvestigation(
                data
            );

    } catch (error) {

        container.innerHTML =
            renderError(
                error.message
            );
    }
}


function renderInvestigation(
    data
) {

    const status =
        data.status
        || "UNKNOWN";

    const attributes =
        data.affected_attributes
        ||
        [];

    let html =
        `
        <div class="${
            status.includes(
                "COMPLETE"
            )
            ? "warning"
            : "success"
        }">

            <strong>
                Status:
            </strong>

            ${escapeHtml(
                status
            )}

        </div>
        `;

    if (
        attributes.length > 0
    ) {

        html +=
            `
            <h3>
                Affected Attributes
            </h3>

            <p>

                ${
                    attributes
                        .map(
                            value => `
                                <span class="tag">

                                    ${escapeHtml(
                                        value
                                    )}

                                </span>
                            `
                        )
                        .join(" ")
                }

            </p>
            `;
    }

    const investigations =
        data.investigations
        || [];

    for (
        const investigation
        of investigations
    ) {

        html +=
            `
            <h3>

                ${escapeHtml(
                    investigation.attribute
                )}

            </h3>
            `;

        const locations =
            investigation
                .likely_code_locations
            || [];

        for (
            const location
            of locations
        ) {

            html +=
                `
                <div class="code-location">

                    ${escapeHtml(
                        location.class_name
                        || ""
                    )}.${escapeHtml(
                        location.method_name
                        || ""
                    )}

                    ${
                        location.line_number
                        ? ` — line ${
                            location.line_number
                        }`
                        : ""
                    }

                    ${
                        location.usage_type
                        ? ` — ${
                            escapeHtml(
                                location.usage_type
                            )
                        }`
                        : ""
                    }

                </div>
                `;
        }

        const trace =
            investigation.trace
                ?.trace
            || [];

        if (
            trace.length > 0
        ) {

            html +=
                `
                <h3>
                    Attribute Trace
                </h3>

                <div class="flow-list">
                `;

            trace.forEach(
                (
                    step,
                    index
                ) => {

                    html +=
                        `
                        <div class="flow-step">

                            ${escapeHtml(
                                step.label
                            )}

                        </div>
                        `;

                    if (
                        index <
                        trace.length - 1
                    ) {

                        html +=
                            `
                            <div class="flow-arrow">
                                ↓
                            </div>
                            `;
                    }
                }
            );

            html +=
                `
                </div>
                `;
        }
    }

    html +=
        `
        <details>

            <summary>
                Full Investigation JSON
            </summary>

            <pre>
${escapeHtml(
    JSON.stringify(
        data,
        null,
        2
    )
)}
            </pre>

        </details>
        `;

    return html;
}


async function analyseRegression() {

    const container =
        document.getElementById(
            "regressionResult"
        );

    container.innerHTML =
        "Checking Git changes...";

    try {

        const response =
            await fetch(
                "/api/regression/impact"
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    data
                )
            );
        }

        container.innerHTML =
            renderRegression(
                data
            );

    } catch (error) {

        container.innerHTML =
            renderError(
                error.message
            );
    }
}


function renderRegression(
    data
) {

    if (
        data.status ===
        "NO_CHANGES"
    ) {

        return `
            <div class="success">
                No Java source changes detected.
            </div>
        `;
    }

    let html =
        `
        <div class="warning">

            <strong>

                ${escapeHtml(
                    data.status
                    || "CHANGES_DETECTED"
                )}

            </strong>

            <div>

                Changed Java files:

                ${
                    data.total_changed_java_files
                    || 0
                }

            </div>

        </div>
        `;

    const methods =
        data.changed_methods
        || [];

    if (
        methods.length > 0
    ) {

        html +=
            "<h3>Changed Methods</h3>";

        for (
            const method
            of methods
        ) {

            html +=
                `
                <div class="code-location">

                    ${escapeHtml(
                        method.class_name
                    )}.${escapeHtml(
                        method.method_name
                    )}

                    ${
                        method.changed_lines
                            ?.length
                        ? ` — lines ${
                            method.changed_lines
                                .join(", ")
                        }`
                        : ""
                    }

                </div>
                `;
        }
    }

    const scenarios =
        data.affected_scenarios
        || [];

    if (
        scenarios.length === 0
    ) {

        html +=
            `
            <div class="success">

                No registered scenario baseline
                currently matches the changed classes.

            </div>
            `;

        return html;
    }

    html +=
        "<h3>Affected Scenarios</h3>";

    for (
        const scenario
        of scenarios
    ) {

        html +=
            `
            <div class="danger">

                <strong>

                    ${escapeHtml(
                        scenario.scenario_code
                    )}

                </strong>

                <div>

                    ${escapeHtml(
                        scenario.http_method
                    )}

                    ${escapeHtml(
                        scenario.endpoint
                    )}

                </div>

                <div>

                    ${escapeHtml(
                        scenario.impact_status
                    )}

                </div>

                <div>

                    Baseline V${
                        scenario.baseline_version
                    }

                </div>

            </div>
            `;
    }

    return html;
}


async function loadBaselineHistory() {

    const scenarioId =
        document.getElementById(
            "baselineScenarioId"
        ).value;

    const container =
        document.getElementById(
            "baselineResult"
        );

    container.innerHTML =
        "Loading baseline history...";

    try {

        const response =
            await fetch(
                `/api/scenario-baselines/history/${scenarioId}`
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    data
                )
            );
        }

        if (
            !Array.isArray(
                data
            )
            ||
            data.length === 0
        ) {

            container.innerHTML =
                "No baselines found.";

            return;
        }

        container.innerHTML =
            data
                .map(
                    baseline => `

                        <div class="${
                            baseline.is_active
                            ? "success"
                            : "result-area"
                        }">

                            <strong>

                                ${escapeHtml(
                                    baseline.scenario_code
                                )}

                            </strong>

                            — Baseline V${
                                baseline.baseline_version
                            }

                            ${
                                baseline.is_active
                                ? " — ACTIVE"
                                : ""
                            }

                            <div>

                                ${escapeHtml(
                                    baseline.http_method
                                )}

                                ${escapeHtml(
                                    baseline.endpoint
                                )}

                            </div>

                            <div>

                                Flow stored:

                                ${
                                    baseline.endpoint_flow
                                    ? "YES"
                                    : "NO"
                                }

                            </div>

                        </div>
                    `
                )
                .join("");

    } catch (error) {

        container.innerHTML =
            renderError(
                error.message
            );
    }
}


async function generateFlowchart() {

    const method =
        document.getElementById(
            "chartMethod"
        ).value;

    const endpoint =
        document.getElementById(
            "chartEndpoint"
        ).value;

    const container =
        document.getElementById(
            "flowchartResult"
        );

    if (!endpoint) {

        container.innerHTML =
            renderError(
                "Please select an endpoint."
            );

        return;
    }

    container.innerHTML =
        "Generating flowchart...";

    try {

        const url =
            "/api/reports/flowchart"
            + "?http_method="
            + encodeURIComponent(
                method
            )
            + "&endpoint="
            + encodeURIComponent(
                endpoint
            );

        const response =
            await fetch(
                url
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                JSON.stringify(
                    data
                )
            );
        }

        if (!data.mermaid) {

            container.innerHTML =
                renderError(
                    "Flowchart was not generated."
                );

            return;
        }

        const diagramId =
            "mermaid-"
            + Date.now();

        container.innerHTML =
            `
            <div id="${diagramId}">
            </div>

            <details>

                <summary>
                    Mermaid Source
                </summary>

                <pre>
${escapeHtml(
    data.mermaid
)}
                </pre>

            </details>
            `;

        const target =
            document.getElementById(
                diagramId
            );

        const result =
            await window.mermaid.render(
                diagramId
                + "-svg",
                data.mermaid
            );

        target.innerHTML =
            result.svg;

    } catch (error) {

        container.innerHTML =
            renderError(
                error.message
            );
    }
}


function renderError(
    message
) {

    return `
        <div class="danger">
            ${escapeHtml(
                message
            )}
        </div>
    `;
}


function escapeHtml(
    value
) {

    if (
        value === null
        ||
        value === undefined
    ) {

        return "";
    }

    return String(
        value
    )
        .replaceAll(
            "&",
            "&amp;"
        )
        .replaceAll(
            "<",
            "&lt;"
        )
        .replaceAll(
            ">",
            "&gt;"
        )
        .replaceAll(
            '"',
            "&quot;"
        )
        .replaceAll(
            "'",
            "&#039;"
        );
}
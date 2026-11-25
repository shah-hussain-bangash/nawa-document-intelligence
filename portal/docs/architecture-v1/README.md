# Complete end-to-end architecture

Status: proposed design, not an implemented or certified platform.

The six-page vector PDF contains a logical overview and five detailed views:
document/RAG flows; procurement/agents/approval; deployment/security/sovereignty;
domain extensions/forecasting; and delivery/evaluation/operations.

Solid arrows show request, data or workflow dependencies. Dashed arrows show
cross-cutting controls, telemetry, lifecycle actions or conditional routes, with
labels identifying their meaning. Logical modules do not require separate
microservices. Hosted/private models are deployment options, not simultaneous
requirements. Redis/Celery is one queue implementation, not the system of record.

All views share verified tenant context, resource authorisation, classified
processing routes and versioned evidence. LLMs propose; deterministic application
services authorise and calculate. Procurement outcomes remain simulated in the
sandbox. Sovereignty requires service-specific data-flow and operator review.

SVGs are scalable diagrams; PNGs are viewing copies; DOT files are editable
Graphviz sources. Overview.mmd is a simplified editable Mermaid overview. The
existing 26-phase implementation guide defines build order and acceptance gates.
No cloud provisioning or application implementation was performed by drawing
these diagrams.

# mcp-circuit-breaker
A programmable safety layer for the Model Context Protocol (MCP). It detects and breaks agentic infinite loops, preventing "token-burn" and protecting downstream SaaS APIs (Salesforce, Zendesk, Stripe) from repetitive, autonomous failures. Injects semantic overrides to force human intervention when agents hit hallucination thresholds.

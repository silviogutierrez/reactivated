// Served by the reactivated vite plugin (src/plugin.mts). Ambient here so
// framework code — and any consumer reaching for the raw module — gets
// types instead of needing ts-ignores or app-local declarations.
declare module "virtual:reactivated/templates" {
    import type React from "react";

    export function getTemplate(
        context: unknown,
    ): Promise<React.ComponentType<Record<string, unknown>>>;
}

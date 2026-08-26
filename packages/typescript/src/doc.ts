import { getDefaultClient } from "./client";
import { MidasResultError } from "./errors";
import type { OperationOptions } from "./operation";
import type { JsonObject } from "./types";

async function post(endpoint: string, argument: JsonObject | string, options: OperationOptions = {}) {
  return (options.client ?? getDefaultClient()).request<JsonObject>(
    "POST",
    endpoint,
    { Argument: argument } as JsonObject,
    options,
  );
}

export const doc = {
  newProject: (options?: OperationOptions) => post("/doc/NEW", {}, options),
  openProject: (path: string, options?: OperationOptions) => post("/doc/OPEN", path, options),
  closeProject: (options?: OperationOptions) => post("/doc/CLOSE", {}, options),
  save: (options?: OperationOptions) => post("/doc/SAVE", {}, options),
  saveAs: (path: string, options?: OperationOptions) => post("/doc/SAVEAS", path, options),
  stageAs: (
    stageStep: string,
    options: OperationOptions & { exportPath?: string } = {},
  ) => {
    const argument: JsonObject = { STAGE_STEP: stageStep };
    if (options.exportPath !== undefined) argument.EXPORT_PATH = options.exportPath;
    return post("/doc/STAGAS", argument, options);
  },
  importJson: (path: string, options?: OperationOptions) => post("/doc/IMPORT", path, options),
  importMxt: (path: string, options?: OperationOptions) => post("/doc/IMPORTMXT", path, options),
  exportJson: (path: string, options?: OperationOptions) => post("/doc/EXPORT", path, options),
  exportMxt: (path: string, options?: OperationOptions) => post("/doc/EXPORTMXT", path, options),
  analyze: async (analysisType?: string, options: OperationOptions = {}) => {
    const response = await post(
      "/doc/ANAL",
      analysisType ? { TYPE: analysisType } : {},
      options,
    );
    const message = response.message;
    const client = options.client ?? getDefaultClient();
    if (
      client.raiseOnResultError &&
      typeof message === "string" &&
      message.toLowerCase().includes("failed")
    ) {
      throw new MidasResultError(
        `POST /doc/ANAL -> 200, but the analysis did not succeed: ${message}`,
        { statusCode: 200, method: "POST", endpoint: "/doc/ANAL", responseBody: response },
      );
    }
    return response;
  },
} as const;

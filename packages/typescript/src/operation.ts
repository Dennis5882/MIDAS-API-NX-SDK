import { getDefaultClient, type MidasClient } from "./client";
import type { HttpMethod, JsonObject, RequestOptions } from "./types";

export interface OperationMetadata {
  endpoint: string;
  method: Extract<HttpMethod, "GET" | "POST">;
  pythonFunction: string;
  pythonModule: string;
}

export interface OperationOptions extends RequestOptions {
  client?: MidasClient;
}

export type GetOperation = ((options?: OperationOptions) => Promise<JsonObject>) & {
  readonly metadata: OperationMetadata;
};

export type PostOperation<TArgument extends object> = ((
  argument: TArgument,
  options?: OperationOptions,
) => Promise<JsonObject>) & { readonly metadata: OperationMetadata };

export function getResult(command: string, options: OperationOptions = {}): Promise<JsonObject> {
  return (options.client ?? getDefaultClient()).request("GET", command, undefined, options);
}

export function postArgument<TArgument extends object>(
  command: string,
  argument: TArgument,
  options: OperationOptions = {},
): Promise<JsonObject> {
  return (options.client ?? getDefaultClient()).request(
    "POST",
    command,
    { Argument: argument } as JsonObject,
    options,
  );
}

export function defineGetOperation(metadata: OperationMetadata): GetOperation {
  const operation = (options: OperationOptions = {}) => getResult(metadata.endpoint, options);
  return Object.assign(operation, { metadata });
}

export function definePostOperation<TArgument extends object = JsonObject>(
  metadata: OperationMetadata,
): PostOperation<TArgument> {
  const operation = (argument: TArgument, options: OperationOptions = {}) =>
    postArgument(metadata.endpoint, argument, options);
  return Object.assign(operation, { metadata });
}

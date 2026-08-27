import { getDefaultClient, type MidasClient } from "./client";
import type { HttpMethod, JsonObject, Product, RequestOptions } from "./types";

export interface OperationMetadata {
  endpoint: string;
  method: Extract<HttpMethod, "GET" | "POST">;
  products: readonly Product[];
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

export type EmptyPostOperation = ((options?: OperationOptions) => Promise<JsonObject>) & {
  readonly metadata: OperationMetadata;
};

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
  const operation = async (options: OperationOptions = {}) => {
    const client = options.client ?? getDefaultClient();
    client.checkProduct(metadata.products, metadata.endpoint);
    return getResult(metadata.endpoint, { ...options, client });
  };
  return Object.assign(operation, { metadata });
}

export function definePostOperation<TArgument extends object = JsonObject>(
  metadata: OperationMetadata,
): PostOperation<TArgument> {
  const operation = async (argument: TArgument, options: OperationOptions = {}) => {
    const client = options.client ?? getDefaultClient();
    client.checkProduct(metadata.products, metadata.endpoint);
    return postArgument(metadata.endpoint, argument, { ...options, client });
  };
  return Object.assign(operation, { metadata });
}

export function defineEmptyPostOperation(metadata: OperationMetadata): EmptyPostOperation {
  const operation = async (options: OperationOptions = {}) => {
    const client = options.client ?? getDefaultClient();
    client.checkProduct(metadata.products, metadata.endpoint);
    return postArgument(metadata.endpoint, {}, { ...options, client });
  };
  return Object.assign(operation, { metadata });
}

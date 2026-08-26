import { getDefaultClient } from "./client";
import type { OperationOptions } from "./operation";
import type { JsonObject, JsonValue } from "./types";

export interface NodeElementsSelector {
  keys?: number[];
  to?: string;
  structureGroupName?: string;
}

export interface TableUnit {
  force?: string;
  distance?: string;
  heat?: string;
  temperature?: string;
}

export interface TableStyles {
  format?: string;
  decimalPlaces?: number;
}

export interface TableOptions extends OperationOptions {
  tableName?: string;
  exportPath?: string;
  nodeElements?: NodeElementsSelector;
  unit?: TableUnit;
  styles?: TableStyles;
  components?: string[];
  loadCaseNames?: string[];
  constructionStage?: boolean;
  stageSteps?: string[];
  parts?: string[];
  storyNames?: string[];
  modes?: string[];
  additional?: Record<string, JsonValue | undefined>;
  calculationMethod?: Record<string, JsonValue | undefined>;
}

function compactRecord(values: Record<string, JsonValue | undefined>): JsonObject {
  return Object.fromEntries(Object.entries(values).filter(([, value]) => value !== undefined));
}

function tableArgument(tableType: string, options: TableOptions): JsonObject {
  const argument = compactRecord({
    TABLE_NAME: options.tableName ?? "",
    TABLE_TYPE: tableType,
    EXPORT_PATH: options.exportPath,
    NODE_ELEMS: options.nodeElements
      ? compactRecord({
          KEYS: options.nodeElements.keys,
          TO: options.nodeElements.to,
          STRUCTURE_GROUP_NAME: options.nodeElements.structureGroupName,
        })
      : undefined,
    UNIT: options.unit
      ? compactRecord({
          FORCE: options.unit.force,
          DIST: options.unit.distance,
          HEAT: options.unit.heat,
          TEMP: options.unit.temperature,
        })
      : undefined,
    STYLES: options.styles
      ? compactRecord({ FORMAT: options.styles.format, PLACE: options.styles.decimalPlaces })
      : undefined,
    COMPONENTS: options.components,
    LOAD_CASE_NAMES: options.loadCaseNames,
    OPT_CS: options.constructionStage,
    STAGE_STEP: options.stageSteps,
    PARTS: options.parts,
    STORY_NAMES: options.storyNames,
    MODES: options.modes,
    ADDITIONAL: options.additional as JsonObject | undefined,
    SET_CALCULATION_METHOD: options.calculationMethod as JsonObject | undefined,
  });
  return argument;
}

export async function getTableAt(
  endpoint: string,
  tableType: string,
  options: TableOptions = {},
): Promise<JsonObject> {
  return (options.client ?? getDefaultClient()).request(
    "POST",
    endpoint,
    { Argument: tableArgument(tableType, options) },
    options,
  );
}

export function getTable(tableType: string, options: TableOptions = {}): Promise<JsonObject> {
  return getTableAt("/post/TABLE", tableType, options);
}

export function unwrapTable(response: JsonObject): JsonObject {
  if ("HEAD" in response || "DATA" in response) return response;
  for (const value of Object.values(response)) {
    if (
      typeof value === "object" &&
      value !== null &&
      !Array.isArray(value) &&
      ("HEAD" in value || "DATA" in value)
    ) {
      return value as JsonObject;
    }
  }
  return {};
}

export type DesignForcesTableOptions = Omit<TableOptions, "loadCaseNames" | "constructionStage" | "stageSteps" | "modes" | "additional" | "calculationMethod">;

function designForces(tableType: string) {
  return (options?: DesignForcesTableOptions) => getTable(tableType, options);
}

export function defineTable(tableType: string) {
  return (options?: TableOptions) => getTable(tableType, options);
}

export function defineVariableTable(defaultTableType?: string) {
  return (options: TableOptions & { tableType?: string } = {}) => {
    const tableType = options.tableType ?? defaultTableType;
    if (!tableType) throw new TypeError("tableType is required");
    return getTable(tableType, options);
  };
}

export function defineDirectionalTable(prefix: string) {
  return (direction: string, options?: TableOptions) => getTable(`${prefix}${direction}`, options);
}

export const post = {
  getTable,
  unwrapTable,
  getBeamDesignForcesTable: designForces("BEAMDESIGNFORCES"),
  getColumnDesignForcesTable: designForces("COLUMNDESIGNFORCES"),
  getBraceDesignForcesTable: designForces("BRACEDESIGNFORCES"),
  getWallDesignForcesTable: designForces("WALLDESIGNFORCES"),
  getSteelMemberDesignForcesTable: designForces("STEELMEMBERDESIGNFORCES"),
  getSrcBeamDesignForcesTable: designForces("SRCBEAMDESIGNFORCES"),
  getSrcColumnDesignForcesTable: designForces("SRCCOLUMNDESIGNFORCES"),
  getColdFormedSteelMemberDesignForcesTable: designForces("COLDFORMEDSTEELMEMBERDESIGNFORCES"),
} as const;

import { designTables, operations, post, resources, tables } from "../src";
import { describe, expect, it } from "vitest";

// This file is compiled by `npm run typecheck`. The unreachable block keeps
// public API examples type-checked without making live requests in Vitest.
if (false) {
  operations.post.design.getPmInteractionDiagram();
  operations.post.design.getSteelCodeCheck();

  tables.preProcess.getMaterialTable({ tableName: "Materials" });
  tables.result1.getReactionTable({
    tableType: "REACTIONL",
    loadCaseNames: ["DL(ST)"],
  });
  tables.story.getStoryModeShapeTable({ modes: ["Mode1"] });
  post.getWallDesignForcesTable({ storyNames: ["1F"] });
  designTables.rcKds.getBeamDesignForcesTable({ exportPath: "C:/reports" });

  // These endpoints shared a legacy Python payload name, but their reviewed
  // contracts differ: DYFG requires HEIGHT_COVER while DYNF permits omission.
  resources.db.movingLoads.railwayDynamicFactor.create({ 1: { INPUT_TYPE: 0, HEIGHT_COVER: 1 } });
  resources.db.movingLoads.railwayDynamicFactorByElement.create({ 1: { INPUT_TYPE: 0 } });

  // @ts-expect-error /db/DYFG requires HEIGHT_COVER in its contract payload
  resources.db.movingLoads.railwayDynamicFactor.create({ 1: { INPUT_TYPE: 0 } });

  // Material tables do not accept analysis-result filters.
  // @ts-expect-error loadCaseNames is not supported by this wrapper
  tables.preProcess.getMaterialTable({ loadCaseNames: ["DL(ST)"] });

  // Mode selection belongs to Story Mode Shape, not Reaction.
  // @ts-expect-error modes is not supported by this wrapper
  tables.result1.getReactionTable({ modes: ["Mode1"] });

  // Directional wrappers only accept the three documented axes.
  // @ts-expect-error invalid direction
  tables.preProcess.getMassSummaryTable("Q");

  // Wall design forces use story selection rather than member-end parts.
  // @ts-expect-error parts is not supported by the wall wrapper
  post.getWallDesignForcesTable({ parts: ["PartI"] });

  // The DESIGN/TABLE endpoint does not accept analysis-result load filters.
  // @ts-expect-error loadCaseNames is not supported by this endpoint
  designTables.rcKds.getBeamDesignForcesTable({ loadCaseNames: ["DL(ST)"] });
}

describe("public type surface", () => {
  it("exposes the generated namespaces at runtime", () => {
    expect(typeof tables.preProcess.getMaterialTable).toBe("function");
    expect(typeof operations.post.design.getPmInteractionDiagram).toBe("function");
  });
});

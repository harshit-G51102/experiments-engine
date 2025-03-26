"use client";

import type React from "react";
import { createContext, useContext, useState } from "react";
import {
  ExperimentState,
  CMABExperimentState,
  CMABArm,
  MABExperimentStateBeta,
  MABExperimentStateNormal,
  ABExperimentState,
  PriorType,
  RewardType,
  MethodType,
  MABArmBeta,
  MABArmNormal,
  ABArm,
  NewContext,
} from "../../types";

type ExperimentContextType = {
  experimentState: ExperimentState;
  setExperimentState: React.Dispatch<React.SetStateAction<ExperimentState>>;
};

const ExperimentContext = createContext<ExperimentContextType | undefined>(
  undefined
);

export const useExperiment = () => {
  const context = useContext(ExperimentContext);
  if (!context) {
    throw new Error("useExperiment must be used within an ExperimentProvider");
  }
  return context;
};

export const ExperimentProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const baseDescr = { name: "", description: "" };
  const [methodType] = useState<MethodType>("mab");
  const [priorType] = useState<PriorType>("beta");
  const [rewardType] = useState<RewardType>("binary");

  const baseMABState = {
    ...baseDescr,
    methodType: methodType,
    rewardType: rewardType,
    priorType: priorType,
    notifications: {
      onTrialCompletion: false,
      numberOfTrials: 0,
      onDaysElapsed: false,
      daysElapsed: 0,
      onPercentBetter: false,
      percentBetterThreshold: 0,
    },
  };

  const [experimentState, setExperimentState] = useState<
    | MABExperimentStateBeta
    | MABExperimentStateNormal
    | ABExperimentState
    | CMABExperimentState
  >(() => {
    if (methodType === "mab") {
      if (priorType === "beta") {
        return {
          ...baseMABState,
          arms: [
            { name: "", description: "", alpha: 1, beta: 1 } as MABArmBeta,
            { name: "", description: "", alpha: 1, beta: 1 } as MABArmBeta,
          ],
        } as MABExperimentStateBeta;
      } else {
        return {
          ...baseMABState,
          arms: [
            { name: "", description: "", mu: 0, sigma: 1 } as MABArmNormal,
            { name: "", description: "", mu: 0, sigma: 1 } as MABArmNormal,
          ],
        } as MABExperimentStateNormal;
      }
    } else if (methodType === "cmab") {
      const { priorType, ...rest } = baseMABState;
      return {
        ...rest,
        priorType: priorType === "normal" ? priorType : "normal",
        arms: [
          { name: "", description: "", mu_init: 0, sigma_init: 1 } as CMABArm,
          { name: "", description: "", mu_init: 0, sigma_init: 1 } as CMABArm,
        ],
        contexts: [
          { name: "", description: "", value_type: "binary" } as NewContext,
        ],
      } as CMABExperimentState;
    } else {
      return {
        ...baseMABState,
        arms: [
          {
            name: "",
            description: "",
            mean_posterior: 0,
            stdDev_posterior: 1,
          } as ABArm,
          {
            name: "",
            description: "",
            mean_posterior: 0,
            stdDev_posterior: 1,
          } as ABArm,
        ],
      } as ABExperimentState;
    }
  });

  return (
    <ExperimentContext.Provider value={{ experimentState, setExperimentState }}>
      {children}
    </ExperimentContext.Provider>
  );
};

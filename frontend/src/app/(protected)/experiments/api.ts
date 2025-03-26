import api from "@/utils/api";
import {
  MABExperimentStateNormal,
  MABExperimentStateBeta,
  ABExperimentState,
  CMABExperimentState,
} from "./types";
import { ExperimentState } from "./types";

const createNewExperiment = async ({
  experimentData,
  token,
}: {
  experimentData: ExperimentState;
  token: string | null;
}) => {
  let endpoint: string;
  let newExperimentData:
    | MABExperimentStateNormal
    | MABExperimentStateBeta
    | ABExperimentState
    | CMABExperimentState;
  let convertedData = null;

  if (experimentData.methodType == "mab") {
    endpoint = "/mab/";
    if (experimentData.priorType == "beta") {
      newExperimentData = experimentData as MABExperimentStateBeta;
    } else {
      newExperimentData = experimentData as MABExperimentStateNormal;
    }
    const { methodType, ...rest } = newExperimentData;
    convertedData = {
      name: rest.name,
      description: rest.description,
      reward_type: rest.rewardType,
      prior_type: rest.priorType,
      arms: rest.arms,
      notifications: rest.notifications,
    };
  } else if (experimentData.methodType == "ab") {
    newExperimentData = experimentData as ABExperimentState;
    endpoint = "/ab/";
    const { methodType, ...rest } = newExperimentData;
    convertedData = { ...rest };
  } else if (experimentData.methodType == "cmab") {
    newExperimentData = experimentData as CMABExperimentState;
    endpoint = "/contextual_mab/";
    const { methodType, ...rest } = newExperimentData;
    convertedData = {
      name: rest.name,
      description: rest.description,
      reward_type: rest.rewardType,
      prior_type: rest.priorType,
      arms: rest.arms,
      notifications: rest.notifications,
      contexts: rest.contexts,
    };
  } else {
    throw new Error("Invalid experiment type");
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    console.log(convertedData);
    const response = await api.post(endpoint, convertedData, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error creating new experiment: ${error.message}`);
  }
};

const getAllMABExperiments = async (token: string | null) => {
  try {
    const response = await api.get("/mab/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error fetching all experiments: ${error.message}`);
  }
};

const getAllCMABExperiments = async (token: string | null) => {
  try {
    const response = await api.get("/contextual_mab/", {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error fetching all experiments: ${error.message}`);
  }
};

export { createNewExperiment, getAllMABExperiments, getAllCMABExperiments };

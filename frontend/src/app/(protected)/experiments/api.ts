import api from "@/utils/api";
import { MABExperimentStateNormal, MABExperimentStateBeta, ABExperimentState } from "./types";
import { ExperimentState } from "./types";

const createNewExperiment = async ({
  experimentData,
  token,
}: {
  experimentData: ExperimentState;
  token: string | null;
}) => {
  let endpoint: string;
  let newExperimentData: MABExperimentStateNormal | MABExperimentStateBeta | ABExperimentState;

  if (experimentData.methodType == "mab") {
    endpoint = "/mab/";
    if (experimentData.priorType == "beta") {
      newExperimentData = experimentData as MABExperimentStateBeta;
    } else {
      newExperimentData = experimentData as MABExperimentStateNormal;
    }

  } else if (experimentData.methodType == "ab") {
    newExperimentData = experimentData as ABExperimentState;
    endpoint = "/ab/";
  } else {
    throw new Error("Invalid experiment type");
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { methodType, ...rest } = newExperimentData;

    const convertedData = {
      name: rest.name,
      description: rest.description,
      reward_type: rest.rewardType,
      prior_type: rest.priorType,
      arms: rest.arms,
      notifications: rest.notifications,
    }

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

export { createNewExperiment, getAllMABExperiments };

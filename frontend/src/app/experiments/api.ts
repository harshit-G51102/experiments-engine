import api from "@/utils/api";
import { NewMAB, MAB, NewCMAB, CMAB } from "./types";

const createMABExperiment = async ({
  mab,
  token,
}: {
  mab: NewMAB;
  token: string | null;
}) => {
  try {
    const response = await api.post("/mab/", mab, {
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

const deleteMABExperiment = async ({
  mab,
  token
} : {
  mab: MAB;
  token: string | null;
}) => {
  try {
    const response = await api.delete(`/mab/${mab.experiment_id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error deleting experiment: ${error.message}`);
}
};

const createCMABExperiment = async ({
  mab,
  token,
}: {
  mab: NewCMAB;
  token: string | null;
}) => {
  console.log(mab);
  try {
    const response = await api.post("/contextual_mab/", mab, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    console.log(error);
    throw new Error(`Error creating new experiment: ${error.message}`);
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

const deleteCMABExperiment = async ({
  mab,
  token
} : {
  mab: CMAB;
  token: string | null;
}) => {
  try {
    const response = await api.delete(`/contextual_mab/${mab.experiment_id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error: any) {
    throw new Error(`Error deleting experiment: ${error.message}`);
}
}

export {
  createMABExperiment, getAllMABExperiments, deleteMABExperiment,
  createCMABExperiment, getAllCMABExperiments, deleteCMABExperiment};

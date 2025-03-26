import { useCallback, useState, useEffect } from "react";
import { Radio, RadioField, RadioGroup } from "@/components/catalyst/radio";
import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
  Description,
} from "@/components/catalyst/fieldset";
import {
  PriorType,
  RewardType,
  StepComponentProps,
  StepValidation,
} from "../../../types";
import { useExperiment } from "../AddExperimentContext";
import { Heading } from "@/components/catalyst/heading";
import { DividerWithTitle } from "@/components/Dividers";

// TODO: not clean to add descriptions here -- should move to types or somewhere else
const priorTypeInfo: Record<PriorType, { name: string; description: string }> =
  {
    beta: {
      name: "Beta Prior",
      description: "Best for binary outcomes",
    },
    normal: {
      name: "Normal Prior",
      description: "Best for real-valued outcomes",
    },
  };

export default function MABPriorRewardSelection({
  onValidate,
}: StepComponentProps) {
  const { experimentState, setExperimentState } = useExperiment();
  const [errors, setErrors] = useState({
    priorType: "",
    rewardType: "",
  });

  const setPriorType = (value: keyof PriorType) => {
    setExperimentState((prevState) => {
      return {
        ...prevState,
        priorType: value as PriorType,
      };
    });
  };

  const setRewardType = (value: keyof RewardType) => {
    setExperimentState((prevState) => {
      return {
        ...prevState,
        rewardType: value as RewardType,
      };
    });
  };

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = {
      priorType: "",
      rewardType: "",
    };

    if (!experimentState.priorType) {
      newErrors.priorType = "Please select a prior type";
      isValid = false;
    }

    if (!experimentState.rewardType) {
      newErrors.rewardType = "Please select a reward type";
      isValid = false;
    }

    if (
      experimentState.priorType === "normal" &&
      experimentState.rewardType === "binary"
    ) {
      newErrors.rewardType =
        "Normal prior is not compatible with binary reward";
      isValid = false;
    }
    if (
      experimentState.priorType === "beta" &&
      experimentState.rewardType === "real-valued"
    ) {
      newErrors.rewardType =
        "Beta prior is not compatible with real-valued reward";
      isValid = false;
    }
    setErrors(newErrors);
    return { isValid, newErrors };
  }, [experimentState.priorType, experimentState.rewardType]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      setErrors(newErrors);
      onValidate({ isValid, errors: newErrors });
    }
  }, [validateForm, onValidate, errors]);

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Configure MAB Parameters</Heading>
      </div>
      <Fieldset aria-label="MAB Parameters" className="pt-6">
        <DividerWithTitle title="Prior Type" />
        <RadioGroup
          name="priorType"
          defaultValue=""
          onChange={(value) => setPriorType(value as keyof PriorType)}
          value={experimentState.priorType}
        >
          <div className="mb-4" />
          <Label>Select prior type for the experiment</Label>
          <RadioField>
            <Radio id="normal" value="normal" />
            <Label htmlFor="normal">Normal</Label>
            <Description>
              Gaussian distribution; best for real-valued outcomes.
            </Description>
          </RadioField>

          <RadioField>
            <Radio id="beta" value="beta" />
            <Label htmlFor="beta">Beta</Label>
            <Description>
              Beta distribution; best for binary outcomes.
            </Description>
          </RadioField>
        </RadioGroup>
        {errors.priorType ? (
          <p className="text-red-500 text-xs mt-1">{errors.priorType}</p>
        ) : (
          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
        )}

        <DividerWithTitle title="Outcome Type" />
        <RadioGroup
          name="rewardType"
          defaultValue=""
          onChange={(value) => setRewardType(value as keyof RewardType)}
          value={experimentState.rewardType}
        >
          <div className="mb-4" />
          <Label>Select an outcome type for the experiment</Label>
          <RadioField>
            <Radio id="real-valued" value="real-valued" />
            <Label htmlFor="real-valued">Real-valued</Label>
            <Description>
              E.g. how long someone engaged with your app, how long did
              onboarding take, etc.
            </Description>
          </RadioField>

          <RadioField>
            <Radio id="binary" value="binary" />
            <Label htmlFor="binary">Binary</Label>
            <Description>
              E.g. whether a user clicked on a button, whether a user converted,
              etc.
            </Description>
          </RadioField>
        </RadioGroup>
        {errors.rewardType ? (
          <p className="text-red-500 text-xs mt-1">{errors.rewardType}</p>
        ) : (
          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
        )}
      </Fieldset>
    </div>
  );
}

import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
  Description,
} from "@/components/catalyst/fieldset";
import { useState, useEffect, useCallback } from "react";
import { Radio, RadioField, RadioGroup } from "@/components/catalyst/radio";
import { Input } from "@/components/catalyst/input";
import { Textarea } from "@/components/catalyst/textarea";
import { AllSteps } from "./addExperimentSteps";
import { useExperiment } from "./AddExperimentContext";
import { Heading } from "@/components/catalyst/heading";
import {
  MABExperimentState,
  NewMABArm,
  NewABArm,
  ABExperimentState,
  StepValidation,
} from "../../types";

type Methods = typeof AllSteps;

export default function AddBasicInfo({
  setMethodType,
  onValidate,
}: {
  setMethodType: (method: keyof Methods) => void;
  onValidate: (validation: StepValidation) => void;
}) {
  const { experimentState, setExperimentState } = useExperiment();
  const [errors, setErrors] = useState({
    name: "",
    description: "",
    methodType: "",
  });

  const defaultMABArms: NewMABArm[] = [
    { name: "", description: "", alpha: 1, beta: 1 },
    { name: "", description: "", alpha: 1, beta: 1 },
  ];
  const defaultABArms: NewABArm[] = [
    { name: "", description: "", mean_prior: 0, stdDev_prior: 1 },
    { name: "", description: "", mean_prior: 0, stdDev_prior: 1 },
  ];

  const methodSelect = (value: keyof Methods) => {
    setMethodType(value);
    // TODO: It's not clean to have this component worr about each experiment type,
    // We should move this elsewhere.
    setExperimentState((prevState) => {
      if (value === "mab") {
        return {
          ...prevState,
          methodType: "mab",
          arms: defaultMABArms,
        } as MABExperimentState;
      } else {
        return {
          ...prevState,
          methodType: "ab",
          arms: defaultABArms,
        } as ABExperimentState;
      }
    });
  };

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = { name: "", description: "", methodType: "" };

    if (!experimentState.name.trim()) {
      newErrors.name = "Experiment name is required";
      isValid = false;
    }

    if (!experimentState.description.trim()) {
      newErrors.description = "Description is required";
      isValid = false;
    }

    if (!experimentState.methodType) {
      newErrors.methodType = "Please select an experiment type";
      isValid = false;
    }

    return { isValid, newErrors };
  }, [experimentState]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      setErrors(newErrors);
      onValidate({ isValid, errors: newErrors });
    }
  }, [validateForm, onValidate, errors]);

  return (
    <div>
      <div className="pt-5 flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Start a new experiment</Heading>
      </div>
      <Fieldset aria-label="New MAB Experiment" className="pt-6">
        <FieldGroup>
          <Field>
            <Label>Experiment Name</Label>
            <Input
              name="experiment-name"
              placeholder="Give it a name you'll remember"
              value={experimentState.name}
              onChange={(e) => {
                setExperimentState({
                  ...experimentState,
                  name: e.target.value,
                });
              }}
            />
            {errors.name ? (
              <p className="text-red-500 text-xs mt-1">{errors.name}</p>
            ) : (
              <p className="text-red-500 text-xs mt-1">&nbsp;</p>
            )}
          </Field>
          <Field>
            <Label>Description</Label>
            <Textarea
              name="experiment-description"
              placeholder="Why are you running this experiment? What do you wish to test?"
              value={experimentState.description}
              rows={3}
              onChange={(e) => {
                setExperimentState({
                  ...experimentState,
                  description: e.target.value,
                });
              }}
            />
            {errors.description ? (
              <p className="text-red-500 text-xs mt-1">{errors.description}</p>
            ) : (
              <p className="text-red-500 text-xs mt-1">&nbsp;</p>
            )}
          </Field>
        </FieldGroup>

        <RadioGroup
          name="experiment-method"
          value={experimentState.methodType}
          onChange={(value) => methodSelect(value as keyof Methods)}
        >
          <Label>Select experiment type</Label>
          <RadioField>
            <Radio id="mab" value="mab" />
            <Label htmlFor="mab">Multi-armed Bandit</Label>
            <Description>
              A method that automatically converges to the best performing arm.
            </Description>
          </RadioField>
          <RadioField>
            <Radio id="ab-test" value="ab" disabled />
            <Label htmlFor="ab-test">[Coming soon] A/B Testing</Label>
            <Description>
              A method that compares two or more variants against each other.
            </Description>
          </RadioField>
        </RadioGroup>
        {errors.methodType ? (
          <p className="text-red-500 text-xs mt-1">{errors.methodType}</p>
        ) : (
          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
        )}
      </Fieldset>
    </div>
  );
}

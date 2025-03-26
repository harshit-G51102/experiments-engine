import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
} from "@/components/catalyst/fieldset";
import { Button } from "@/components/catalyst/button";
import { Input } from "@/components/catalyst/input";
import { Textarea } from "@/components/catalyst/textarea";
import { useExperiment } from "../AddExperimentContext";
import {
  CMABExperimentState,
  NewCMABArm,
  StepComponentProps,
} from "../../../types";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { TrashIcon } from "@heroicons/react/16/solid";
import { Heading } from "@/components/catalyst/heading";
import { useCallback, useEffect, useMemo, useState } from "react";

export default function AddCMABArms({ onValidate }: StepComponentProps) {
  const { experimentState, setExperimentState } = useExperiment();

  const baseArmDesc = useMemo(
    () => ({
      name: "",
      description: "",
    }),
    []
  );

  const additionalArmErrors = useMemo(
    () => ({ mu_init: "", sigma_init: "" }),
    []
  );

  const additionalArmDesc = useMemo(() => ({ mu_init: 0, sigma_init: 1 }), []);

  const [errors, setErrors] = useState(() => {
    return experimentState.arms.map(() => {
      return { ...baseArmDesc, ...additionalArmErrors };
    });
  });

  const arms = useCallback(() => {
    if (experimentState.methodType === "cmab") {
      return experimentState.arms as NewCMABArm[];
    }
    return [] as NewCMABArm[];
  }, [experimentState])();

  const defaultArm = { ...baseArmDesc, ...additionalArmDesc };

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = arms.map(() => ({
      ...baseArmDesc,
      ...additionalArmErrors,
    }));

    arms.forEach((arm, index) => {
      if (!arm.name.trim()) {
        newErrors[index].name = "Arm name is required";
        isValid = false;
      }

      if (!arm.description.trim()) {
        newErrors[index].description = "Description is required";
        isValid = false;
      }

      if ("mu_init" in arm && typeof arm.mu_init !== "number") {
        newErrors[index].mu_init = "Mean value is required";
        isValid = false;
      }

      if ("sigma_init" in arm) {
        if (!arm.sigma_init) {
          newErrors[index].sigma_init = "Std. deviation is required";
          isValid = false;
        }
        if (arm.sigma_init < 0) {
          newErrors[index].sigma_init =
            "Std deviation should be greater than 0";
          isValid = false;
        }
      }
    });

    return { isValid, newErrors };
  }, [arms, baseArmDesc, additionalArmErrors]);

  useEffect(() => {
    const { isValid, newErrors } = validateForm();
    if (JSON.stringify(newErrors) !== JSON.stringify(errors)) {
      setErrors(newErrors);
      onValidate({
        isValid,
        errors: newErrors.map((error) =>
          Object.fromEntries(
            Object.entries(error).map(([key, value]) => [key, value ?? ""])
          )
        ),
      });
    }
  }, [validateForm, onValidate, errors]);

  useEffect(() => {
    if (experimentState.methodType === "cmab") {
      const convertedArms = experimentState.arms.map((arm) => {
        const newArm = {
          name: arm.name || "",
          description: arm.description || "",
          mu_init: "mu_init" in arm ? arm.mu_init : 0,
          sigma_init: "sigma_init" in arm ? arm.sigma_init : 1,
        } as NewCMABArm;
        return newArm;
      });

      // Update experiment state with converted arms
      setExperimentState({
        ...experimentState,
        arms: convertedArms as typeof experimentState.arms,
      });
    }
  }, [experimentState, setExperimentState]);

  const typeSafeSetExperimentState = (newArms: NewCMABArm[]) => {
    if (experimentState.methodType === "cmab") {
      setExperimentState({
        ...experimentState,
        arms: newArms,
      } as CMABExperimentState);
    } else {
      console.error("Method type is not CMAB");
      throw new Error("Method type is not CMAB");
    }
  };

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Add CMAB Arms</Heading>
        <div className="flex gap-4">
          <Button
            className="mt-4"
            onClick={() =>
              setExperimentState((prevState) => {
                if (prevState.methodType === "cmab") {
                  return {
                    ...prevState,
                    arms: [
                      ...(prevState.arms as NewCMABArm[]),
                      defaultArm as NewCMABArm,
                    ],
                  };
                } else {
                  console.error("Method type is not CMAB");
                  throw new Error("Method type is not CMAB");
                }
              })
            }
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Arm
          </Button>
          <Button
            className="mt-4 mx-4"
            disabled={arms.length <= 2}
            outline
            onClick={() => {
              if (experimentState.methodType === "cmab") {
                setExperimentState({
                  ...experimentState,
                  arms: experimentState.arms.slice(
                    0,
                    experimentState.arms.length - 1
                  ) as NewCMABArm[],
                });
              } else {
                console.error("Method type is not MAB");
                throw new Error("Method type is not MAB");
              }
            }}
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Delete Arm
          </Button>
        </div>
      </div>
      <Fieldset aria-label="Add MAB Arms">
        {arms.map((arm, index) => (
          <div key={index}>
            <DividerWithTitle title={`Arm ${index + 1}`} />
            <FieldGroup
              key={index}
              className="md:flex md:flex-row md:space-x-8 md:space-y-0 items-start"
            >
              <div className="basis-1/2">
                <Field className="flex flex-col mb-4">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium">Name</Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        name={`arm-${index + 1}-name`}
                        placeholder="Give the arm a searchable name"
                        value={arm.name || ""}
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].name = e.target.value;
                          typeSafeSetExperimentState(newArms as NewCMABArm[]);
                        }}
                      />
                      {errors[index]?.name ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].name}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
                <Field className="flex flex-col">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium">
                      Description
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Textarea
                        name={`arm-${index + 1}-description`}
                        placeholder="Describe the arm"
                        value={arm.description || ""}
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].description = e.target.value;
                          typeSafeSetExperimentState(newArms as NewCMABArm[]);
                        }}
                      />
                      {errors[index]?.description ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].description}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
              </div>

              <div className="basis-1/2 grow">
                <Field className="flex flex-col mb-4">
                  <div className="flex flex-row">
                    <Label className="basis-1/4 mt-3 font-medium" htmlFor="mu">
                      Mean prior
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        id={`arm-${index + 1}-mu_init`}
                        name={`arm-${index + 1}-mu_init`}
                        type="number"
                        placeholder="Enter a float as mean for the prior"
                        defaultValue={0}
                        value={
                          "mu_init" in arm
                            ? arm.mu_init === 0
                              ? "0"
                              : arm.mu_init || ""
                            : ""
                        }
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].mu_init = parseFloat(e.target.value);
                          typeSafeSetExperimentState(newArms as NewCMABArm[]);
                        }}
                      />
                      {errors[index]?.mu_init ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].mu_init}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
                <Field className="flex flex-col">
                  <div className="flex flex-row">
                    <Label
                      className="basis-1/4 mt-3 font-medium"
                      htmlFor="sigma"
                    >
                      Standard deviation
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <Input
                        id={`arm-${index + 1}-sigma`}
                        name={`arm-${index + 1}-sigma`}
                        type="number"
                        defaultValue={1}
                        placeholder="Enter a float as standard deviation for the prior"
                        value={
                          "sigma_init" in arm
                            ? arm.sigma_init === 0
                              ? "0"
                              : arm.sigma_init || ""
                            : ""
                        }
                        onChange={(e) => {
                          const newArms = [...arms];
                          newArms[index].sigma_init = parseFloat(
                            e.target.value
                          );
                          typeSafeSetExperimentState(newArms as NewCMABArm[]);
                        }}
                      />
                      {errors[index]?.sigma_init ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].sigma_init}
                        </p>
                      ) : (
                        <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                      )}
                    </div>
                  </div>
                </Field>
              </div>
            </FieldGroup>
          </div>
        ))}
      </Fieldset>
    </div>
  );
}

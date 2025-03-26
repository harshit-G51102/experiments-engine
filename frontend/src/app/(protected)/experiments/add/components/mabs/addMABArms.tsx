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
  MABExperimentStateNormal,
  MABExperimentStateBeta,
  NewMABArmBeta,
  NewMABArmNormal,
  StepComponentProps,
} from "../../../types";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { TrashIcon } from "@heroicons/react/16/solid";
import { Heading } from "@/components/catalyst/heading";
import { useCallback, useEffect, useState, useMemo } from "react";

export default function AddMABArms({ onValidate }: StepComponentProps) {
  const { experimentState, setExperimentState } = useExperiment();

  const baseArmDesc = useMemo(
    () => ({
      name: "",
      description: "",
    }),
    []
  );

  const additionalArmErrors = useMemo(
    () =>
      experimentState.priorType === "beta"
        ? { alpha: "", beta: "" }
        : { mu: "", sigma: "" },
    [experimentState]
  );

  const additionalArmDesc = useMemo(
    () =>
      experimentState.priorType === "beta"
        ? { alpha: 1, beta: 1 }
        : { mu: 0, sigma: 1 },
    [experimentState]
  );

  const [errors, setErrors] = useState(() => {
    return experimentState.arms.map(() => {
      return { ...baseArmDesc, ...additionalArmErrors };
    });
  });

  const arms = useCallback(() => {
    return experimentState.methodType === "mab" &&
      experimentState.priorType === "beta"
      ? (experimentState.arms as NewMABArmBeta[])
      : (experimentState.arms as NewMABArmNormal[]);
  }, [experimentState])();

  const defaultArm = useMemo(
    () => ({ ...baseArmDesc, ...additionalArmDesc }),
    [baseArmDesc, additionalArmDesc]
  );

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

      if (experimentState.priorType === "beta") {
        if ("alpha" in arm) {
          if (!arm.alpha) {
            newErrors[index].alpha = "Alpha prior is required";
            isValid = false;
          }
          if (arm.alpha <= 0) {
            newErrors[index].alpha = "Alpha prior should be greater than 0";
            isValid = false;
          }
        }

        if ("beta" in arm) {
          if (!arm.beta) {
            newErrors[index].beta = "Beta prior is required";
            isValid = false;
          }

          if (arm.beta <= 0) {
            newErrors[index].beta = "Beta prior should be greater than 0";
            isValid = false;
          }
        }
      } else if (experimentState.priorType === "normal") {
        if ("mu" in arm && typeof arm.mu !== "number") {
          newErrors[index].mu = "Mean value is required";
          isValid = false;
        }

        if ("sigma" in arm) {
          if (!arm.sigma) {
            newErrors[index].sigma = "Std. deviation is required";
            isValid = false;
          }

          if (arm.sigma <= 0) {
            newErrors[index].sigma = "Std deviation should be greater than 0";
            isValid = false;
          }
        }
      }
    });
    return { isValid, newErrors };
  }, [arms, experimentState, baseArmDesc, additionalArmErrors]);

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
    if (experimentState.methodType === "mab") {
      // Update experiment state with converted arms
      if (experimentState.priorType === "beta") {
        setExperimentState({
          ...experimentState,
          arms: experimentState.arms as NewMABArmBeta[],
        });
      } else if (experimentState.priorType === "normal") {
        setExperimentState({
          ...experimentState,
          arms: experimentState.arms as NewMABArmNormal[],
        });
      }
    }
  }, [experimentState, arms, setExperimentState]); // Only run when prior type changes

  const typeSafeSetExperimentState = (
    newArms: NewMABArmBeta[] | NewMABArmNormal[]
  ) => {
    if (experimentState.methodType === "mab") {
      if (experimentState.priorType === "beta") {
        setExperimentState({
          ...experimentState,
          arms: newArms as NewMABArmBeta[],
        } as MABExperimentStateBeta);
      } else if (experimentState.priorType === "normal") {
        setExperimentState({
          ...experimentState,
          arms: newArms as NewMABArmNormal[],
        } as MABExperimentStateNormal);
      }
    } else {
      console.error("Method type is not MAB");
      throw new Error("Method type is not MAB");
    }
  };

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Add MAB Arms</Heading>
        <div className="flex gap-4">
          <Button
            className="mt-4"
            onClick={() =>
              setExperimentState((prevState) => {
                if (prevState.methodType === "mab") {
                  if (experimentState.priorType === "beta") {
                    return {
                      ...prevState,
                      arms: [
                        ...(prevState.arms as NewMABArmBeta[]),
                        defaultArm as NewMABArmBeta,
                      ],
                    };
                  } else if (experimentState.priorType === "normal") {
                    return {
                      ...prevState,
                      arms: [
                        ...(prevState.arms as NewMABArmNormal[]),
                        defaultArm as NewMABArmNormal,
                      ],
                    };
                  } else {
                    throw new Error("Unsupported prior type");
                  }
                } else {
                  console.error("Method type is not MAB");
                  throw new Error("Method type is not MAB");
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
              if (experimentState.methodType === "mab") {
                experimentState.priorType === "beta"
                  ? setExperimentState({
                      ...experimentState,
                      arms: experimentState.arms.slice(
                        0,
                        experimentState.arms.length - 1
                      ) as NewMABArmBeta[],
                    })
                  : experimentState.priorType === "normal"
                  ? setExperimentState({
                      ...experimentState,
                      arms: experimentState.arms.slice(
                        0,
                        experimentState.arms.length - 1
                      ) as NewMABArmNormal[],
                    })
                  : setExperimentState({
                      ...experimentState,
                      arms: experimentState.arms.slice(
                        0,
                        experimentState.arms.length - 1
                      ) as NewMABArmBeta[],
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
                          if (experimentState.priorType === "beta") {
                            typeSafeSetExperimentState(
                              newArms as NewMABArmBeta[]
                            );
                          } else if (experimentState.priorType === "normal") {
                            typeSafeSetExperimentState(
                              newArms as NewMABArmNormal[]
                            );
                          }
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
                          if (experimentState.priorType === "beta") {
                            typeSafeSetExperimentState(
                              newArms as NewMABArmBeta[]
                            );
                          } else if (experimentState.priorType === "normal") {
                            typeSafeSetExperimentState(
                              newArms as NewMABArmNormal[]
                            );
                          }
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
              {experimentState.priorType === "beta" && (
                <div className="basis-1/2 grow">
                  <Field className="flex flex-col mb-4">
                    <div className="flex flex-row">
                      <Label
                        className="basis-1/4 mt-3 font-medium"
                        htmlFor="alpha"
                      >
                        Alpha prior
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-alpha`}
                          name={`arm-${index + 1}-alpha`}
                          placeholder="Enter an integer as the prior for the alpha parameter"
                          value={
                            experimentState.priorType === "beta" &&
                            "alpha" in arm
                              ? arm.alpha || ""
                              : ""
                          }
                          onChange={(e) => {
                            const newArms = [...arms];
                            if (
                              experimentState.priorType === "beta" &&
                              "alpha" in newArms[index]
                            ) {
                              newArms[index].alpha = parseInt(e.target.value);
                            }
                            typeSafeSetExperimentState(
                              newArms as NewMABArmBeta[]
                            );
                          }}
                        />
                        {errors[index]?.alpha ? (
                          <p className="text-red-500 text-xs mt-1">
                            {errors[index].alpha}
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
                        htmlFor="beta"
                      >
                        Beta prior
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-beta`}
                          name={`arm-${index + 1}-beta`}
                          placeholder="Enter an integer as the prior for the beta parameter"
                          value={
                            experimentState.priorType === "beta" &&
                            "beta" in arm
                              ? arm.beta || ""
                              : ""
                          }
                          onChange={(e) => {
                            const newArms = [...arms];
                            if (
                              experimentState.priorType === "beta" &&
                              "beta" in newArms[index]
                            ) {
                              newArms[index].beta = parseInt(e.target.value);
                            }
                            typeSafeSetExperimentState(
                              newArms as NewMABArmBeta[]
                            );
                          }}
                        />
                        {errors[index]?.beta ? (
                          <p className="text-red-500 text-xs mt-1">
                            {errors[index].beta}
                          </p>
                        ) : (
                          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                        )}
                      </div>
                    </div>
                  </Field>
                </div>
              )}
              {experimentState.priorType === "normal" && (
                <div className="basis-1/2 grow">
                  <Field className="flex flex-col mb-4">
                    <div className="flex flex-row">
                      <Label
                        className="basis-1/4 mt-3 font-medium"
                        htmlFor="mu"
                      >
                        Mean prior
                      </Label>
                      <div className="basis-3/4 flex flex-col">
                        <Input
                          id={`arm-${index + 1}-mu`}
                          name={`arm-${index + 1}-mu`}
                          type="number"
                          placeholder="Enter a float as mean for the prior"
                          defaultValue={0}
                          value={
                            experimentState.priorType === "normal" &&
                            "mu" in arm
                              ? arm.mu === 0
                                ? "0"
                                : arm.mu || ""
                              : ""
                          }
                          onChange={(e) => {
                            const newArms = [...arms];
                            if (
                              experimentState.priorType === "normal" &&
                              "mu" in newArms[index]
                            ) {
                              newArms[index].mu = parseFloat(e.target.value);
                            }
                            typeSafeSetExperimentState(
                              newArms as NewMABArmNormal[]
                            );
                          }}
                        />
                        {errors[index]?.mu ? (
                          <p className="text-red-500 text-xs mt-1">
                            {errors[index].mu}
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
                            experimentState.priorType === "normal" &&
                            "sigma" in arm
                              ? arm.sigma === 0
                                ? "0"
                                : arm.sigma || ""
                              : ""
                          }
                          onChange={(e) => {
                            const newArms = [...arms];
                            if (
                              experimentState.priorType === "normal" &&
                              "sigma" in newArms[index]
                            ) {
                              newArms[index].sigma = parseFloat(e.target.value);
                            }
                            typeSafeSetExperimentState(
                              newArms as NewMABArmNormal[]
                            );
                          }}
                        />
                        {errors[index]?.sigma ? (
                          <p className="text-red-500 text-xs mt-1">
                            {errors[index].sigma}
                          </p>
                        ) : (
                          <p className="text-red-500 text-xs mt-1">&nbsp;</p>
                        )}
                      </div>
                    </div>
                  </Field>
                </div>
              )}
            </FieldGroup>
          </div>
        ))}
      </Fieldset>
    </div>
  );
}

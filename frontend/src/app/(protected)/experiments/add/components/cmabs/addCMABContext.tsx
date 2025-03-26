import {
  Field,
  FieldGroup,
  Fieldset,
  Label,
  Description,
} from "@/components/catalyst/fieldset";
import { Button } from "@/components/catalyst/button";
import { Input } from "@/components/catalyst/input";
import { Textarea } from "@/components/catalyst/textarea";
import { useExperiment } from "../AddExperimentContext";
import {
  CMABExperimentState,
  NewCMABArm,
  StepComponentProps,
  ContextType,
  NewContext,
} from "../../../types";
import { PlusIcon } from "@heroicons/react/16/solid";
import { DividerWithTitle } from "@/components/Dividers";
import { TrashIcon } from "@heroicons/react/16/solid";
import { Heading } from "@/components/catalyst/heading";
import { useCallback, useEffect, useState, useRef } from "react";
import { Radio, RadioGroup, RadioField } from "@/components/catalyst/radio";

export default function AddCMABContext({ onValidate }: StepComponentProps) {
  const { experimentState, setExperimentState } = useExperiment();
  const { methodType } = experimentState;
  const muInputRefs = useRef<HTMLInputElement[]>([]);

  const defaultContext = {
    name: "",
    description: "",
    value_type: "",
  };

  useEffect(() => {
    if (methodType === "cmab") {
      if (
        !experimentState.contexts ||
        !Array.isArray(experimentState.contexts) ||
        experimentState.contexts.length === 0
      ) {
        console.log("Initializing contexts with default context");
        setExperimentState({
          ...experimentState,
          contexts: [{ ...defaultContext }] as NewContext[],
        });
      }
    }
  }, [methodType]);

  const [errors, setErrors] = useState(() => {
    if (
      methodType === "cmab" &&
      experimentState.contexts &&
      Array.isArray(experimentState.contexts)
    ) {
      return experimentState.contexts.map(() => {
        return { ...defaultContext };
      });
    } else {
      return [{ ...defaultContext }];
    }
  });

  const contexts =
    methodType === "cmab" && experimentState.contexts
      ? (experimentState.contexts as NewContext[])
      : [];

  const validateForm = useCallback(() => {
    let isValid = true;
    const newErrors = contexts.map(() => ({
      ...defaultContext,
    }));

    contexts.forEach((context, index) => {
      if (!context.name.trim()) {
        newErrors[index].name = "Context name is required";
        isValid = false;
      }

      if (!context.description.trim()) {
        newErrors[index].description = "Description is required";
        isValid = false;
      }

      if (!context.value_type.trim()) {
        newErrors[index].value_type = "Context value type is required";
        isValid = false;
      }
    });

    return { isValid, newErrors };
  }, [contexts]);

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
    if (experimentState.methodType === "cmab" && experimentState.contexts) {
      const convertedContexts = experimentState.contexts.map((context) => ({
        name: context.name || "",
        description: context.description || "",
        value_type: context.value_type || "real-valued",
      }));

      setExperimentState({
        ...experimentState,
        contexts: convertedContexts as NewContext[],
      });
    }
  }, [methodType]);

  const typeSafeSetExperimentState = (newContexts: NewContext[]) => {
    if (experimentState.methodType === "cmab") {
      setExperimentState({
        ...experimentState,
        contexts: newContexts,
      } as CMABExperimentState);
    } else {
      console.error("Method type is not CMAB");
      throw new Error("Method type is not CMAB");
    }
  };

  return (
    <div>
      <div className="flex w-full flex-wrap items-end justify-between gap-4 border-b border-zinc-950/10 pb-6 dark:border-white/10">
        <Heading>Add CMAB Contexts</Heading>
        <div className="flex gap-4">
          <Button
            className="mt-4"
            onClick={() =>
              setExperimentState((prevState) => {
                if (prevState.methodType === "cmab") {
                  return {
                    ...prevState,
                    contexts: [
                      ...(prevState.contexts as NewContext[]),
                      {
                        ...defaultContext,
                        context_id: Date.now(),
                      } as NewContext,
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
            Add Context
          </Button>
          <Button
            className="mt-4 mx-4"
            disabled={contexts.length <= 1}
            outline
            onClick={() => {
              if (experimentState.methodType === "cmab") {
                setExperimentState({
                  ...experimentState,
                  contexts: experimentState.contexts.slice(
                    0,
                    experimentState.contexts.length - 1
                  ) as NewContext[],
                });
              } else {
                console.error("Method type is not MAB");
                throw new Error("Method type is not MAB");
              }
            }}
          >
            <TrashIcon className="w-4 h-4 mr-2" />
            Delete Context
          </Button>
        </div>
      </div>
      <Fieldset aria-label="Add Contexts">
        {contexts.map((context, index) => (
          <div key={index}>
            <DividerWithTitle title={`Context ${index + 1}`} />
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
                        name={`context-${index + 1}-name`}
                        placeholder="Give the context a searchable name"
                        value={context.name || ""}
                        onChange={(e) => {
                          const newContexts = [...contexts];
                          newContexts[index].name = e.target.value;
                          typeSafeSetExperimentState(
                            newContexts as NewContext[]
                          );
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
                        name={`context-${index + 1}-description`}
                        placeholder="Describe the context"
                        value={context.description || ""}
                        onChange={(e) => {
                          const newContexts = [...contexts];
                          newContexts[index].description = e.target.value;
                          typeSafeSetExperimentState(
                            newContexts as NewContext[]
                          );
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
                      Context type
                    </Label>
                    <div className="basis-3/4 flex flex-col">
                      <RadioGroup
                        name={`context-${index}-value-type`}
                        defaultValue=""
                        value={context.value_type || ""}
                        onChange={(value) => {
                          const newContexts = [...contexts];
                          newContexts[index].value_type = value as ContextType;
                          typeSafeSetExperimentState(
                            newContexts as NewContext[]
                          );
                        }}
                      >
                        <div className="space-y-2">
                          <RadioField className="flex items-start space-x-2 rounded-md border border-gray-800 p-3 hover:bg-gray-800/50 transition-colors">
                            <Radio
                              id={`context-${index}-binary`}
                              value="binary"
                            />
                            <div className="flex flex-col">
                              <Label
                                htmlFor={`context-${index}-binary`}
                                className="font-medium"
                              >
                                Binary
                              </Label>
                            </div>
                          </RadioField>

                          <RadioField className="flex items-start space-x-2 rounded-md border border-gray-800 p-3 hover:bg-gray-800/50 transition-colors">
                            <Radio
                              id={`context-${index}-real-valued`}
                              value="real-valued"
                            />
                            <div className="flex flex-col">
                              <Label
                                htmlFor={`context-${index}-real-valued`}
                                className="font-medium"
                              >
                                Real-valued
                              </Label>
                            </div>
                          </RadioField>
                        </div>
                      </RadioGroup>

                      {errors[index]?.value_type ? (
                        <p className="text-red-500 text-xs mt-1">
                          {errors[index].value_type}
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

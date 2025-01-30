interface NewContext {
  name: string;
  description: string;
  context_type: string|null;
  values: number[];
  weight: number;

}

interface Context extends NewContext {
  context_id: number;
}

interface NewArm {
  name: string;
  description: string;
  alpha_prior: number;
  beta_prior: number;
}

interface Arm extends NewArm {
  arm_id: number;
  successes: number;
  failures: number;
}

interface ContextualArm extends NewArm {
  arm_id: number;
  successes: number[];
  failures: number[];
}

interface NewMAB {
  name: string;
  description: string;
  arms: NewArm[];
}

interface NewCMAB extends NewMAB {
  arms: NewArm[];
  contexts: NewContext[];
}

interface MAB extends NewMAB {
  experiment_id: number;
  is_active: boolean;
  arms: Arm[];
}

interface CMAB extends NewCMAB {
  experiment_id: number;
  is_active: boolean;
  arms: ContextualArm[];
  contexts: Context[];
}

interface BetaParams {
  name: string;
  alpha: number;
  beta: number;
}

export type {
  Arm,
  Context,
  ContextualArm,
  CMAB,
  MAB,
  NewArm,
  NewContext,
  NewCMAB,
  NewMAB,
  BetaParams };

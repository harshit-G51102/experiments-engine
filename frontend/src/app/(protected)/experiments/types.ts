type MethodType = "mab" | "ab";
type RewardType = "binary" | "real-valued";
type PriorType = "beta" | "normal";

interface BetaParams {
  name: string;
  alpha: number;
  beta: number;
}

interface StepComponentProps {
  onValidate: (validation: StepValidation) => void;
}

interface Step {
  name: string;
  component: React.FC<StepComponentProps>;
}

type Notifications = {
  onTrialCompletion?: boolean;
  numberOfTrials?: number;
  onDaysElapsed?: boolean;
  daysElapsed?: number;
  onPercentBetter?: boolean;
  percentBetterThreshold?: number;
};

interface ExperimentStateBase {
  name: string;
  description: string;
  methodType: MethodType;
  priorType: PriorType;
  rewardType: RewardType;
}

interface ArmBase {
  name: string;
  description: string;
}

interface StepValidation {
  isValid: boolean;
  errors: Record<string, string> | Record<string, string>[];
}
// ----- AB

interface NewABArm extends ArmBase {
  mean_prior: number;
  stdDev_prior: number;
}

interface ABArm extends NewABArm {
  arm_id: number;
  mean_posterior: number;
  stdDev_posterior: number;
}

interface ABExperimentState extends ExperimentStateBase {
  methodType: "ab";
  arms: NewABArm[];
  notifications: Notifications;
}

interface AB extends ABExperimentState {
  experiment_id: number;
  is_active: boolean;
  arms: ABArm[];
}

// ----- MAB

interface NewMABArmBeta extends ArmBase {
  alpha: number;
  beta: number;
}

interface NewMABArmNormal extends ArmBase {
  mu: number;
  sigma: number;
}

interface MABArmBeta extends NewMABArmBeta {
  arm_id: number;
}

interface MABArmNormal extends NewMABArmNormal {
  arm_id: number;
}

interface MABExperimentStateNormal extends ExperimentStateBase {
  methodType: "mab";
  arms: NewMABArmNormal[];
  notifications: Notifications;
}

interface MABExperimentStateBeta extends ExperimentStateBase {
  methodType: "mab";
  arms: NewMABArmBeta[];
  notifications: Notifications;
}

interface MABNormal extends MABExperimentStateNormal {
  experiment_id: number;
  is_active: boolean;
  arms: MABArmNormal[];
}

interface MABBeta extends MABExperimentStateBeta {
  experiment_id: number;
  is_active: boolean;
  arms: MABArmBeta[];
}

type ExperimentState = MABExperimentStateNormal | MABExperimentStateBeta | ABExperimentState;

export type {
  AB,
  ABArm,
  ABExperimentState,
  ArmBase,
  BetaParams,
  ExperimentState,
  ExperimentStateBase,
  MABBeta,
  MABNormal,
  MABArmBeta,
  MABArmNormal,
  MABExperimentStateBeta,
  MABExperimentStateNormal,
  MethodType,
  NewABArm,
  NewMABArmBeta,
  NewMABArmNormal,
  Notifications,
  PriorType,
  RewardType,
  Step,
  StepComponentProps,
  StepValidation,
};

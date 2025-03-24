import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { MABBeta, MABNormal, CMAB, BetaParams, MethodType } from "../types";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { BetaLineChart } from "./Charts";
import { MABBetaCards, MABNormalCards } from "./cards/createMABCard";
import { Trash2 } from "lucide-react";

export default function ExperimentCards({ experiment, methodType }:
  { experiment: MABBeta | MABNormal | CMAB, methodType: MethodType }) {
  const [isHovered, setIsHovered] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

if (methodType === "mab" && experiment.prior_type === "beta") {
  const betaExperiment = experiment as MABBeta;
  return MABBetaCards({
    experiment: betaExperiment,
    successes: [3, 1],
    failures: [0, 3],
    isHovered,
    setIsHovered,
    isExpanded,
    setIsExpanded });
} else if (methodType === "mab" && experiment.prior_type === "normal") {
  const normalExperiment = experiment as MABNormal;
  return MABNormalCards({
    experiment: normalExperiment,
    mu_final: [2.5, -1.3],
    sigma_final: [1.5, 2.3],
    isHovered,
    setIsHovered,
    isExpanded,
    setIsExpanded,
  });
}

// Default case for other experiment types
return (
  <Card>
    <CardContent>
      <CardTitle>Unsupported Experiment Type</CardTitle>
      <CardDescription>This experiment type is not yet supported.</CardDescription>
    </CardContent>
  </Card>
);
}

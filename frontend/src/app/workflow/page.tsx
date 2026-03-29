"use client";

import { useState } from "react";
import type { WorkflowInfo } from "@/types";
import { WorkflowSelector, WorkflowPanel } from "@/components/workflow";
import { useWorkflowStore } from "@/stores/workflowStore";
import { cn } from "@/lib/utils";

export default function WorkflowPage() {
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowInfo | null>(
    null
  );
  const { reset } = useWorkflowStore();

  const handleSelect = (workflow: WorkflowInfo) => {
    setSelectedWorkflow(workflow);
  };

  const handleBack = () => {
    reset();
    setSelectedWorkflow(null);
  };

  return (
    <main
      className={cn(
        "flex-1 h-screen overflow-hidden",
        "bg-gray-50 dark:bg-gray-950"
      )}
    >
      {selectedWorkflow ? (
        <WorkflowPanel workflow={selectedWorkflow} onBack={handleBack} />
      ) : (
        <div className="h-full overflow-y-auto">
          <WorkflowSelector onSelect={handleSelect} />
        </div>
      )}
    </main>
  );
}

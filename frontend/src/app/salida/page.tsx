import { Suspense } from "react";
import ExitForm from "./ExitForm";

export default function ExitPage() {
  return (
    <Suspense fallback={null}>
      <ExitForm />
    </Suspense>
  );
}

import { Suspense } from "react";
import PaymentsScreen from "./PaymentsScreen";

export default function PaymentsPage() {
  return (
    <Suspense fallback={null}>
      <PaymentsScreen />
    </Suspense>
  );
}

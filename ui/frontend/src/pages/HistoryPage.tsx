import HistoryTable from "../components/HistoryTable";
import type { RunHistoryItem } from "../types";

interface Props {
  refreshKey: number;
  onReRun: (item: RunHistoryItem) => void;
}

export default function HistoryPage({ refreshKey, onReRun }: Props) {
  return <HistoryTable onReRun={onReRun} refreshKey={refreshKey} />;
}

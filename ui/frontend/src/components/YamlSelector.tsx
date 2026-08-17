import { useEffect, useState } from "react";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
} from "@mui/material";
import { api } from "../api/client";
import type { YamlInfo } from "../types";

interface Props {
  value: string;
  onChange: (val: string) => void;
  disabled?: boolean;
}

export default function YamlSelector({ value, onChange, disabled }: Props) {
  const [yamls, setYamls] = useState<YamlInfo[]>([]);

  useEffect(() => {
    api.listYamls().then(setYamls).catch(() => {});
  }, []);

  return (
    <FormControl size="small" sx={{ minWidth: 200 }}>
      <InputLabel>YAML Source</InputLabel>
      <Select
        value={value}
        label="YAML Source"
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      >
        {yamls.map((y) => (
          <MenuItem key={y.path} value={y.path}>
            {y.name}
            {y.kind === "profile" ? " (profile)" : y.kind === "source" ? " (source)" : ""}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

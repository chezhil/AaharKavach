"use client";

import { History, ScanLine } from "lucide-react";
import Link from "next/link";
import { HistoryRow } from "@/components/history/HistoryRow";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";
import { useApp } from "@/lib/store/app-store";

export default function HistoryPage() {
  const { history } = useApp();

  return (
    <div className="space-y-4">
      <header className="px-1">
        <h1 className="display text-2xl">Scan history</h1>
        <p className="mt-1 text-sm text-fg-subtle">
          Every product you&apos;ve checked, newest first. Tap one to re-run it
          against whoever is selected now.
        </p>
      </header>

      {history.length === 0 ? (
        <EmptyState
          icon={History}
          title="Nothing scanned yet"
          body="Scanned products land here so you can re-check a brand without hunting for the packet."
          action={
            <Link href="/">
              <Button variant="secondary" size="sm">
                <ScanLine size={15} />
                Scan something
              </Button>
            </Link>
          }
        />
      ) : (
        <ul className="grid gap-2 md:grid-cols-2 lg:grid-cols-3">
          {history.map((scan) => (
            <HistoryRow key={scan.id} scan={scan} />
          ))}
        </ul>
      )}
    </div>
  );
}

import { useState } from "react";
import { Alert, Linking, View } from "react-native";
import * as A from "../../src/api";
import { useAuth } from "../../src/auth";
import { useLoad } from "../../src/useLoad";
import { PAYFAST_FIELDS, PAYFAST_UNSUPPORTED_REQUIRED } from "../../src/payfast-config";
import { downloadProtected } from "../../src/files";
import {
  AlertBox,
  Badge,
  Button,
  Card,
  Empty,
  Field,
  Loading,
  Row,
  Screen,
  Stat,
  dateZA,
  money,
} from "../../src/components";

export default function Finance() {
  const auth = useAuth();
  const { data: r, error, loading } = useLoad(A.finance);
  const [amount, setAmount] = useState("");
  const [actionError, setActionError] = useState("");
  const [busy, setBusy] = useState(false);

  if (loading) return <Loading text="Loading finance..." />;

  const d = r?.data || {};
  const s = d.summary || {};

  async function download(path: string, name: string) {
    setActionError("");
    try {
      await downloadProtected(path, auth.token, name);
    } catch (e: any) {
      setActionError(e?.message || "Download failed.");
    }
  }

  async function pay() {
    if (PAYFAST_UNSUPPORTED_REQUIRED.length) {
      Alert.alert(
        "PayFast configuration",
        `Mobile PayFast needs support for: ${PAYFAST_UNSUPPORTED_REQUIRED.join(", ")}`
      );
      return;
    }

    const value = Number(amount || s.outstanding_balance || 0);
    if (
      PAYFAST_FIELDS.includes("amount") ||
      PAYFAST_FIELDS.includes("payment_amount")
    ) {
      if (!Number.isFinite(value) || value <= 0) {
        setActionError("Enter a valid payment amount.");
        return;
      }
    }

    const payload: any = {};

    if (PAYFAST_FIELDS.includes("amount")) payload.amount = value;
    if (PAYFAST_FIELDS.includes("payment_amount")) payload.payment_amount = value;
    if (PAYFAST_FIELDS.includes("student_number")) {
      payload.student_number = auth.meta?.student_number;
    }

    setBusy(true);
    setActionError("");

    try {
      const response = await A.startPayfast(payload, auth.token);
      const q = response?.result || response?.data || response || {};
      const url =
        q.payment_url ||
        q.redirect_url ||
        q.checkout_url ||
        q.url ||
        q.action_url;

      if (url && !q.fields && !q.form_fields) {
        await Linking.openURL(url);
      } else if (url) {
        Alert.alert(
          "PayFast ready",
          "The backend returned a POST-form checkout flow. The final release build will open this inside the secure payment WebView."
        );
      } else {
        throw new Error("No PayFast redirect URL was returned.");
      }
    } catch (e: any) {
      setActionError(e?.message || "Payment could not be started.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Screen
      eyebrow="Finance"
      title="My Student Account"
      subtitle="View your account, invoices, payments and receipts."
    >
      <AlertBox error={error || actionError} />

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 10, marginBottom: 13 }}>
        <Stat label="Total Charges" value={money(s.total_charges)} />
        <Stat label="Payments" value={money(s.payments_total)} />
        <Stat label="Outstanding" value={money(s.outstanding_balance)} />
        <Stat label="Funding Type" value={d?.account?.funding_type || "Not set"} />
      </View>

      <Card title="Statement">
        <Button
          title="Download / Share Statement"
          onPress={() =>
            void download(
              "/api/student/finance/documents/statement",
              `Statement_${auth.meta?.student_number}.pdf`
            )
          }
        />
      </Card>

      {Number(s.outstanding_balance || 0) > 0 && (
        <Card title="Pay Online with PayFast">
          {(PAYFAST_FIELDS.includes("amount") ||
            PAYFAST_FIELDS.includes("payment_amount")) && (
            <Field
              label="Amount to Pay"
              keyboardType="decimal-pad"
              value={amount}
              onChangeText={setAmount}
              placeholder={String(s.outstanding_balance || "")}
            />
          )}
          <Button
            title={busy ? "Preparing PayFast..." : "Pay Now"}
            onPress={() => void pay()}
            disabled={busy}
          />
        </Card>
      )}

      <Card title="Invoices">
        {d?.invoices?.length ? (
          d.invoices.map((x: any) => (
            <Row
              key={x.invoice_number}
              title={x.invoice_number}
              subtitle={`${dateZA(x.invoice_date)} · ${money(x.total_amount)}`}
              right={<Badge value={x.status} />}
              onPress={() =>
                void download(
                  `/api/student/finance/documents/invoice/${encodeURIComponent(x.invoice_number)}`,
                  `${x.invoice_number}.pdf`
                )
              }
            />
          ))
        ) : (
          <Empty title="No invoices found" />
        )}
      </Card>

      <Card title="Payments & Receipts">
        {d?.payments?.length ? (
          d.payments.map((x: any) => (
            <Row
              key={x.payment_reference}
              title={x.payment_reference}
              subtitle={`${dateZA(x.payment_date)} · ${x.payment_method} · ${money(x.amount)}`}
              right={<Badge value={x.status} />}
              onPress={
                x.receipt_number
                  ? () =>
                      void download(
                        `/api/student/finance/documents/receipt/${encodeURIComponent(x.receipt_number)}`,
                        `${x.receipt_number}.pdf`
                      )
                  : undefined
              }
            />
          ))
        ) : (
          <Empty title="No payments recorded yet" />
        )}
      </Card>
    </Screen>
  );
}

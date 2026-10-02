import { useEffect, useState } from "react";
import * as A from "../src/api";
import { useAuth } from "../src/auth";
import { AlertBox, Button, Card, Field, Info, Loading, Screen } from "../src/components";

export default function Account() {
  const auth = useAuth();
  const [data, setData] = useState<any>(null);
  const [email, setEmail] = useState("");
  const [cell, setCell] = useState("");
  const [phone, setPhone] = useState("");
  const [language, setLanguage] = useState("");
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [pinPassword, setPinPassword] = useState("");
  const [pin, setPin] = useState("");
  const [pinConfirm, setPinConfirm] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      const response = await A.settings(auth.token);
      const settings = response?.settings || {};
      const q = settings.contact || settings.profile || {};
      setData(settings);
      setEmail(q.email || "");
      setCell(q.cell_number || "");
      setPhone(q.phone_number || "");
      setLanguage(settings.preferences?.preferred_language || "");
    } catch (e: any) {
      setError(e?.message || "Account settings could not be loaded.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [auth.token]);

  async function saveContact() {
    try {
      await A.saveContact(
        {
          email: email || null,
          cell_number: cell || null,
          phone_number: phone || null,
        },
        auth.token
      );
      setMessage("Contact details updated.");
      setError("");
      await load();
    } catch (e: any) {
      setError(e?.message || "Contact details could not be saved.");
    }
  }

  async function saveLanguage() {
    try {
      await A.savePrefs(
        {
          preferred_notification_channel: "Portal",
          preferred_language: language || null,
        },
        auth.token
      );
      setMessage("Preferences updated.");
      setError("");
    } catch (e: any) {
      setError(e?.message || "Preferences could not be saved.");
    }
  }

  async function changePassword() {
    if (next !== confirm) {
      setError("New passwords do not match.");
      return;
    }

    try {
      const response = await A.changePassword({
        student_number: auth.meta?.student_number,
        current_password: current,
        new_password: next,
      });
      const result = response?.result || response;
      await auth.update(result.access_token, {
        login_method: "password_pending_pin",
        must_change_password: false,
        pin_created: result.pin_created !== false,
      });
      setCurrent("");
      setNext("");
      setConfirm("");
      setMessage("Password changed. Sign in with PIN again if requested.");
      setError("");
    } catch (e: any) {
      setError(e?.message || "Password could not be changed.");
    }
  }

  async function savePin() {
    if (pin !== pinConfirm) {
      setError("PIN entries do not match.");
      return;
    }

    try {
      await A.setupPin({
        student_number: auth.meta?.student_number,
        password: pinPassword,
        pin,
      });
      await auth.update(auth.token, { pin_created: true });
      setPinPassword("");
      setPin("");
      setPinConfirm("");
      setMessage("PIN updated.");
      setError("");
    } catch (e: any) {
      setError(e?.message || "PIN could not be updated.");
    }
  }

  if (loading) return <Loading text="Loading account..." />;

  return (
    <Screen
      eyebrow="Profile & Security"
      title="My Account"
      subtitle="Manage contact details, preferences, password and PIN."
    >
      <AlertBox error={error} message={message} />

      <Card title="Student Profile">
        <Info
          label="Student Number"
          value={data?.profile?.student_number || auth.meta?.student_number}
        />
        <Info
          label="Name"
          value={[
            data?.profile?.first_name,
            data?.profile?.middle_name,
            data?.profile?.last_name,
          ]
            .filter(Boolean)
            .join(" ")}
        />
        <Info
          label="Date of Birth"
          value={data?.profile?.birth_date}
        />
      </Card>

      <Card title="Contact Details">
        <Field label="Email" value={email} onChangeText={setEmail} keyboardType="email-address" />
        <Field label="Cell Number" value={cell} onChangeText={setCell} keyboardType="phone-pad" />
        <Field label="Phone Number" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
        <Button title="Save Contact Details" onPress={() => void saveContact()} />
      </Card>

      <Card title="Preferences">
        <Field
          label="Preferred Language"
          value={language}
          onChangeText={setLanguage}
          placeholder="Optional"
        />
        <Button title="Save Preferences" secondary onPress={() => void saveLanguage()} />
      </Card>

      <Card title="Change Password">
        <Field label="Current Password" secureTextEntry value={current} onChangeText={setCurrent} />
        <Field label="New Password" secureTextEntry value={next} onChangeText={setNext} />
        <Field label="Confirm Password" secureTextEntry value={confirm} onChangeText={setConfirm} />
        <Button title="Change Password" secondary onPress={() => void changePassword()} />
      </Card>

      <Card title="Create / Change 5-Digit PIN">
        <Field label="Current Password" secureTextEntry value={pinPassword} onChangeText={setPinPassword} />
        <Field label="New PIN" secureTextEntry keyboardType="number-pad" maxLength={5} value={pin} onChangeText={(v) => setPin(v.replace(/\D/g, ""))} />
        <Field label="Confirm PIN" secureTextEntry keyboardType="number-pad" maxLength={5} value={pinConfirm} onChangeText={(v) => setPinConfirm(v.replace(/\D/g, ""))} />
        <Button title="Save PIN" secondary onPress={() => void savePin()} />
      </Card>
    </Screen>
  );
}

import { expect, test } from "@playwright/test";

const user = { id: 7, name: "Payment Student", email: "pay@example.com", role: "student", is_active: true, is_email_verified: true, onboarding_completed: true };
const paidPlans = [
  { code:"free", name:"Free", amount:"0.00", currency:"LKR", duration_days:null, features:["Basic learning tools"] },
  { code:"premium_30_days", name:"30-Day Premium Access", amount:"500.00", currency:"LKR", duration_days:30, features:["Premium for 30 days"] },
  { code:"premium_365_days", name:"365-Day Premium Access", amount:"5000.00", currency:"LKR", duration_days:365, features:["Premium for 365 days"] },
];

test.setTimeout(120_000);

async function authenticatedPage(page) {
  let profileCalls = 0;
  await page.addInitScript(({ userData }) => {
    localStorage.setItem("learnfy_token", "e2e-token");
    localStorage.setItem("learnfy_user", JSON.stringify(userData));
    HTMLFormElement.prototype.submit = function submit() {
      window.__payhereSubmission = { action:this.action, fields:Object.fromEntries(new FormData(this).entries()) };
    };
  }, { userData:user });
  await page.route("http://localhost:8000/**", route => route.fulfill({ status:404, json:{ detail:"Not mocked in E2E" } }));
  await page.route("**/users/profile*", route => {
    profileCalls += 1;
    return route.fulfill({ json:user });
  });
  await page.route("**/notifications/unread-count*", route => route.fulfill({ json:{ unread_count:0 } }));
  await page.route("**/notifications*", route => route.fulfill({ json:[] }));
  return () => profileCalls;
}

test("PayHere checkout uses the selected server plan and a POST form", async ({ page }) => {
  await authenticatedPage(page);
  let createBody;
  await page.route("**/payments/plans*", route => route.fulfill({ json:{ gateway:"PayHere", mode:"sandbox", configured:true, plans:paidPlans } }));
  await page.route("http://localhost:8000/payments/checkout", async route => {
    createBody = route.request().postDataJSON();
    await new Promise(resolve => setTimeout(resolve, 200));
    return route.fulfill({ json:{ order_id:"LFY-PH-TEST", provider:"payhere",
      checkout_url:"https://sandbox.payhere.lk/pay/checkout", fields:{ merchant_id:"1234567",
      order_id:"LFY-PH-TEST", amount:"500.00", currency:"LKR", hash:"SAFE_SERVER_HASH" } } });
  });
  await page.goto("/payments/checkout?plan=premium_30_days");
  await expect(page.getByRole("heading", { name:"30-Day Premium Access" })).toBeVisible({ timeout:90_000 });
  await page.getByLabel("Phone").fill("0771234567");
  await page.getByLabel("Address").fill("1 Test Road");
  await page.getByLabel("City").fill("Colombo");
  const button = page.getByRole("button", { name:/Continue to PayHere/ });
  await button.click();
  await expect(button).toBeDisabled();
  await expect.poll(() => page.evaluate(() => window.__payhereSubmission)).not.toBeUndefined();
  const submitted = await page.evaluate(() => window.__payhereSubmission);
  expect(createBody.plan_code).toBe("premium_30_days");
  expect(createBody.amount).toBeUndefined();
  expect(submitted.action).toBe("https://sandbox.payhere.lk/pay/checkout");
  expect(submitted.fields).toMatchObject({ order_id:"LFY-PH-TEST", amount:"500.00", currency:"LKR" });
});

test("disabled payments and server-confirmed result states are clear", async ({ page }) => {
  const profileCalls = await authenticatedPage(page);
  await page.route("**/payments/plans*", route => route.fulfill({ json:paidPlans }));
  await page.route("**/payments/config*", route => route.fulfill({ json:{ enabled:false, provider:null, sandbox:true, message:"Payments are currently unavailable" } }));
  await page.goto("/pricing");
  await expect(page.getByRole("button", { name:"Payments are currently unavailable" }).first()).toBeDisabled({ timeout:90_000 });

  let status = "pending";
  await page.route("**/payments/status/ORDER-TEST*", route => route.fulfill({ json:{ payment:{
    order_id:"ORDER-TEST", provider:"payhere", provider_payment_id:"PH-TEST", plan_code:"premium_30_days",
    amount:"500.00", currency:"LKR", status, payment_method:"VISA", status_message:null,
    paid_at:"2026-08-06T00:00:00Z", created_at:"2026-08-06T00:00:00Z" }, subscription:null } }));
  await page.goto("/payments/result?order_id=ORDER-TEST");
  await expect(page.getByRole("heading", { name:/Verifying payment/i })).toBeVisible();
  status = "success";
  await expect(page.getByRole("heading", { name:/Payment confirmed/i })).toBeVisible();
  await expect.poll(profileCalls).toBeGreaterThanOrEqual(2);
  status = "cancelled"; await page.reload();
  await expect(page.getByRole("heading", { name:/Payment cancelled/i })).toBeVisible();
  status = "failed"; await page.reload();
  await expect(page.getByRole("heading", { name:/Payment unsuccessful/i })).toBeVisible();
});

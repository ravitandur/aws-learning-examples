import { Authenticator, ThemeProvider } from '@aws-amplify/ui-react'
import '@aws-amplify/ui-react/styles.css'
import Dashboard from './pages/Dashboard'
import { amplifyTheme } from './components/auth/AmplifyTheme'

// Custom CSS to override Amplify styles
const customStyles = `
  .amplify-authenticator {
    --amplify-components-authenticator-router-background-color: transparent;
    --amplify-components-authenticator-router-border: none;
    --amplify-components-authenticator-router-box-shadow: none;
  }
  
  .amplify-authenticator [data-amplify-router] {
    background: linear-gradient(to bottom right, rgb(59 130 246), rgb(147 51 234), rgb(126 58 242));
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  
  .amplify-authenticator [data-amplify-container] {
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
    max-width: 28rem;
    width: 100%;
    padding: 0;
  }
`

function App() {
  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: customStyles }} />
      <ThemeProvider theme={amplifyTheme}>
        <Authenticator
          formFields={{
            signUp: {
              name: {
                label: 'Full Name',
                placeholder: 'Enter your full name',
                isRequired: true,
              },
              phone_number: {
                label: 'Phone Number',
                placeholder: '+919876543210',
                isRequired: true,
              },
              custom_state: {
                label: 'State',
                placeholder: 'Select your state',
                isRequired: false,
              },
            },
          }}
          components={{
            Header() {
              return (
                <div className="text-center px-8 pt-8 pb-4">
                  <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    Quantleap Analytics
                  </h1>
                  <p className="text-lg text-gray-600">
                    Algorithmic Trading Platform for Indian Markets
                  </p>
                  <div className="mt-3">
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                      AWS Amplify Gen 2
                    </span>
                  </div>
                </div>
              )
            },
          }}
          services={{
            async validateCustomSignUp(formData) {
              // Custom validation for phone number
              if (formData.phone_number && !formData.phone_number.match(/^\+91[6-9]\d{9}$/)) {
                return {
                  phone_number: 'Please enter a valid Indian phone number (+919876543210)',
                };
              }
              return {};
            },
          }}
        >
          {({ signOut, user }) => (
            <Dashboard signOut={signOut} user={user} />
          )}
        </Authenticator>
      </ThemeProvider>
    </>
  )
}

export default App

<!DOCTYPE html>
<html lang="{{ str_replace('_', '-', app()->getLocale()) }}">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <title>Calcify</title>

        <!-- Fonts -->
        <link rel="preconnect" href="https://fonts.bunny.net">
        <link href="https://fonts.bunny.net/css?family=figtree:400,600&display=swap" rel="stylesheet" />

        <!-- Styles -->
        @vite(['resources/css/app.css', 'resources/js/app.js'])
        @livewireStyles
    </head>
    <body class="antialiased font-sans bg-gray-100 dark:bg-gray-900">
        <div class="min-h-screen flex flex-col items-center justify-center">
            <div class="w-full max-w-3xl px-4 py-8">
                <header class="flex flex-col items-center mb-8">
                    <div class="mb-4">
                        <x-application-logo class="w-16 h-16 text-gray-800 dark:text-white" />
                    </div>
                    @if (Route::has('login'))
                        <livewire:welcome.navigation />
                    @endif
                </header>

                <main>
                    <div class="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 flex flex-col items-center">
                        <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-4 text-center">
                            Calcify: Turn Your Sales Into Solid Profit.
                        </h1>
                        <p class="text-lg text-gray-700 dark:text-gray-300 mb-6 text-center">
                            Tired of messy notebooks, confusing spreadsheets, and costly software? Calcify is the open-source solution designed by and for small entrepreneurs.
                        </p>
                        <p class="text-md text-gray-600 dark:text-gray-400 mb-6 text-center">
                            It's more than a calculator; it's the digital backbone that solidifies your business. Effortlessly track products, calculate prices in multiple currencies, and gain total control over your purchases and sales—all from one intuitive web application.
                        </p>
                        <p class="text-md text-gray-600 dark:text-gray-400 mb-6 text-center">
                            With Calcify, managing your home-based warehouse becomes clear, precise, and professional. Best of all, it's completely free, flexible, and continuously improved by a community that shares your vision for success.
                        </p>
                        <p class="text-md text-gray-800 dark:text-gray-200 font-semibold text-center">
                            Stop guessing, start growing. The stability your business needs, now in your hands.
                        </p>
                    </div>
                </main>

                <footer class="mt-8 text-center text-sm text-gray-500 dark:text-gray-400">
                    Laravel v{{ Illuminate\Foundation\Application::VERSION }} (PHP v{{ PHP_VERSION }})
                </footer>
            </div>
        </div>
        @livewireScripts
    </body>
</html>
